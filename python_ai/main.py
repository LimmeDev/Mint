from flask import Flask
from flask_sock import Sock
import json, os, logging

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

MODEL_PATH = os.getenv("LLAMA_MODEL", "~/models/Meta-Llama-3-8B-instruct.Q4_K_M.gguf")

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
sock = Sock(app)

llm = None
if Llama and os.path.exists(os.path.expanduser(MODEL_PATH)):
    llm = Llama(model_path=os.path.expanduser(MODEL_PATH))
    app.logger.info("Llama model loaded ✔")
else:
    app.logger.warning("Running in echo mode – install llama-cpp-python and a GGUF model for real AI decisions.")


@sock.route('/ws')
def ws_route(ws):
    while True:
        snapshot_raw = ws.receive()
        if snapshot_raw is None:
            break
        snapshot = json.loads(snapshot_raw)
        app.logger.debug("Snapshot: %s", snapshot)

        # Produce plan
        plan = generate_plan(snapshot)
        ws.send(json.dumps(plan))


def generate_plan(snapshot: dict) -> dict:
    if llm is None:
        # Simple demo: place a plank every 4 seconds at (0,70,0)
        return {"build": [{"block": "minecraft:oak_planks", "x": 0, "y": 70, "z": 0}]}

    prompt = (
        "You are a Minecraft AI. Given the JSON snapshot below, output a build plan JSON "
        "with an array 'build' of blocks to place. Each entry: {block,x,y,z}.\n" + json.dumps(snapshot)
    )
    try:
        res = llm(prompt, max_tokens=256)
        text = res["choices"][0]["text"]
        brace = text.find("{")
        plan = json.loads(text[brace:]) if brace >= 0 else {}
    except Exception as e:
        app.logger.error("AI generation failed: %s", e)
        plan = {}
    return plan


if __name__ == '__main__':
    app.logger.info("Starting AI server on ws://127.0.0.1:8000/ws …")
    app.run(host='0.0.0.0', port=8000) 