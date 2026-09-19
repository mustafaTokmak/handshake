"""Deploy the shared live demo with: uv run modal deploy modal_app.py."""
from pathlib import Path
import subprocess
import modal

ROOT = Path(__file__).parent
app = modal.App('handshake-live-demo')
image = (modal.Image.debian_slim(python_version='3.12')
         .uv_sync(str(ROOT))
         .add_local_python_source('repair_lab', ignore=['**/__pycache__/**', '**/*.pyc']))


@app.function(
    image=image,
    secrets=[modal.Secret.from_name('handshake-live-demo')],
    env={'REPAIR_PUBLIC_URL': 'https://mtokmak06--handshake-live.modal.run',
         'REPAIR_STATE_DICT': 'handshake-live-demo-state', 'PYDANTIC_AI_NO_BANNER': '1'},
    min_containers=1, max_containers=1, cpu=0.5, memory=512, timeout=3600,
)
@modal.concurrent(max_inputs=40)
@modal.web_server(8780, startup_timeout=60, label='handshake-live')
def live_demo():
    # One warm writer keeps shared state coherent and background repairs alive
    # between browser requests. GPU inference remains on the existing Gateway route.
    subprocess.Popen(['python', '-m', 'repair_lab.cli', '--host', '0.0.0.0', '--port', '8780'])
