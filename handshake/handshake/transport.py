import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path


class LocalTransport:
    async def start(self):
        self.directory = tempfile.TemporaryDirectory(prefix="handshake-provider-")
        # The provider does not need or inherit model/account credentials.
        env = {key: value for key, value in os.environ.items() if key in ("PATH", "SYSTEMROOT", "TMPDIR", "LANG")}
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
        self.process = await asyncio.create_subprocess_exec(sys.executable, "-u", "-m", "handshake.worker", str(Path(self.directory.name)/"ledger.sqlite"), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env)
        self.lock = asyncio.Lock()
        self.broken = False

    async def rpc(self, payload: dict) -> dict:
        async with self.lock:
            if self.broken:
                raise RuntimeError("Provider channel interrupted; evaluation is unavailable")
            try:
                self.process.stdin.write((json.dumps(payload)+"\n").encode())
                await self.process.stdin.drain()
                line = await asyncio.wait_for(self.process.stdout.readline(), timeout=15)
                if not line:
                    raise RuntimeError("Provider process exited unexpectedly")
                response = json.loads(line)
            except BaseException:
                # Never consume a late tool reply as the reply to a later evaluation.
                self.broken = True
                raise
            if not response["ok"]:
                raise RuntimeError(f"Provider rejected request: {response['error']}: {response['detail']}")
            return response["result"]

    async def close(self):
        if hasattr(self, "process") and self.process.returncode is None:
            self.process.stdin.close()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=3)
            except TimeoutError:
                self.process.kill()
                await self.process.wait()
        if hasattr(self, "directory"):
            self.directory.cleanup()


class ModalTransport:
    async def start(self):
        import modal

        self.lock = asyncio.Lock()
        self.broken = False
        package = Path(__file__).resolve().parent
        image = modal.Image.debian_slim(python_version="3.12").pip_install("pydantic>=2.12,<3").add_local_dir(str(package), remote_path="/app/handshake", ignore=["__pycache__", "static"])
        app = await modal.App.lookup.aio("handshake-provider", create_if_missing=True)
        self.sandbox = await modal.Sandbox.create.aio(image=image, app=app, timeout=600, idle_timeout=120, workdir="/app", block_network=True)
        self.process = await self.sandbox.exec.aio("python", "-u", "-m", "handshake.worker", "/tmp/ledger.sqlite", timeout=540, bufsize=1)
        self.lines = self.process.stdout.__aiter__()

    async def rpc(self, payload: dict) -> dict:
        async with self.lock:
            if self.broken:
                raise RuntimeError("Provider channel interrupted; evaluation is unavailable")
            try:
                self.process.stdin.write((json.dumps(payload)+"\n").encode())
                await self.process.stdin.drain.aio()
                line = await asyncio.wait_for(anext(self.lines), timeout=30)
                response = json.loads(line)
            except BaseException:
                self.broken = True
                raise
            if not response["ok"]:
                raise RuntimeError(f"Provider rejected request: {response['error']}: {response['detail']}")
            return response["result"]

    async def close(self):
        if hasattr(self, "sandbox"):
            try:
                await self.sandbox.terminate.aio()
            finally:
                await self.sandbox.detach.aio()
