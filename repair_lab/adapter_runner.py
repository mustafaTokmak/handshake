"""Runs ONLY inside a fresh network-disabled Modal sandbox. No verdicts live here."""
import contextlib
import io
import json
import resource
import sys

resource.setrlimit(resource.RLIMIT_CPU, (4, 4))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
payload = json.loads(sys.stdin.readline())
try:
    namespace = {}
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exec(compile(payload["source"], "candidate_adapter.py", "exec"), namespace)
        result = namespace[payload["function"]](payload["argument"])
    print("REPAIR_RESULT:" + json.dumps({"ok": True, "result": result}, allow_nan=False))
except BaseException as exc:
    print("REPAIR_RESULT:" + json.dumps({"ok": False, "error": type(exc).__name__, "detail": str(exc)[:600]}))
