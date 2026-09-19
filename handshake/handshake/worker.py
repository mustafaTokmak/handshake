"""Private JSON-lines RPC. Evaluator operations are not registered as agent tools."""
import json
import sys

from .provider import Provider


def main():
    provider = Provider(sys.argv[1])
    for line in sys.stdin:
        try:
            request = json.loads(line)
            op = request["op"]
            if op == "initialize":
                result = provider.initialize(request["scenario"])
            elif op == "tool":
                result = provider.call(request["tool"], request["arguments"])
            elif op == "evaluate":
                result = provider.evaluate(request["order_id"], request["request_key"], request["outcome"])
            else:
                raise ValueError("Unknown operation")
            print(json.dumps({"ok": True, "result": result}), flush=True)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": type(exc).__name__, "detail": str(exc)}), flush=True)


if __name__ == "__main__":
    main()
