import argparse
import os
from pathlib import Path
import logfire
from dotenv import dotenv_values
from .server import serve

PROJECT = Path(__file__).resolve().parent.parent

def main():
    for k, v in dotenv_values(PROJECT/".env").items():
        if v: os.environ.setdefault(k, v)
    parser = argparse.ArgumentParser(description="Handshake carrier API repair lab")
    parser.add_argument("--port", type=int, default=8780)
    parser.add_argument("--state-dir", type=Path, default=PROJECT/"state")
    args = parser.parse_args()
    logfire.configure(service_name="handshake-repair", send_to_logfire=bool(os.getenv("LOGFIRE_TOKEN")), console=False, inspect_arguments=False)
    logfire.instrument_pydantic_ai()
    serve(args.port, args.state_dir)

if __name__ == "__main__": main()
