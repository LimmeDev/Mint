from flask import Flask, request, jsonify
import json, os, pathlib, logging

try:
    from llama_cpp import Llama  # Heavy import, optional
except ImportError:
    Llama = None  # Fallback if llama-cpp-python isn't installed

###############################################################
# Configuration
###############################################################
# Path to your GGUF file. Override via the LLAMA_MODEL env-var.
MODEL_PATH = pathlib.Path(os.environ.get("LLAMA_MODEL", "~/models/Meta-Llama-3-8B-instruct.Q4_K_M.gguf")).expanduser()

# Inference params – tweak to taste / hardware
LLAMA_KWARGS = {
    "n_ctx": int(os.environ.get("LLAMA_CTX", 4096)),
    "n_threads": int(os.environ.get("LLAMA_THREADS", os.cpu_count() or 4)),
}

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

###############################################################
# Optional: load the model at startup (will take a while)
###############################################################
llm = None
if Llama is None:
    app.logger.warning("`llama-cpp-python` not installed – AI will echo inputs. Run `pip install llama-cpp-python --upgrade`.")
else:
    if MODEL_PATH.exists():
        app.logger.info(f"Loading Llama-3 model from {MODEL_PATH} … this can take 1-2 minutes on first run.")
        try:
            llm = Llama(model_path=str(MODEL_PATH), **LLAMA_KWARGS)
            app.logger.info("Model loaded successfully ✔")
        except Exception as exc:
            app.logger.error(f"Failed to load Llama model: {exc}")
    else:
        app.logger.warning(f"Model file not found at {MODEL_PATH}. AI will echo inputs.")

###############################################################
# Helper – generate an AI plan or fallback
###############################################################

def generate_plan(snapshot: dict) -> dict:
    """Return a dict plan given a game snapshot."""
    if llm is None:
        # Fallback – just acknowledge the call
        return {"message": "AI inactive – install model to enable decisions."}

    sys_prompt = (
        "You are the autonomous governor of a Captain of Industry colony. "
        "Decide the next actions. Respond ONLY in JSON with this exact schema:\n"
        "{ 'build': [ { 'type': str, 'recipe': str|none, 'x': int, 'y': int } ], "
        "'research': str|none, 'actions': [ { 'kind': str, 'target': str, 'value': str } ] }"
    )
    user_prompt = json.dumps(snapshot, indent=2)
    prompt = f"[SYSTEM]{sys_prompt}\n[USER]{user_prompt}\n[ASSISTANT]"

    try:
        completion = llm(prompt, max_tokens=512, stop=["[STOP]"])
        raw_text = completion["choices"][0]["text"]
        brace = raw_text.find("{")
        json_text = raw_text[brace:] if brace >= 0 else "{}"
        return json.loads(json_text)
    except Exception as exc:
        app.logger.error(f"AI generation failed: {exc}")
        return {"message": "AI generation error – see server logs."}

###############################################################
# Flask route – entry point for the CoI mod
###############################################################

@app.route('/', methods=['POST'])
def handle_game_data():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    snapshot = request.get_json(force=True)
    app.logger.debug("Received snapshot: %s", json.dumps(snapshot)[:2000])

    plan = generate_plan(snapshot)
    return jsonify(plan)

###############################################################
# Main
###############################################################

if __name__ == '__main__':
    host = os.environ.get("AI_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("AI_SERVER_PORT", 8000))
    app.logger.info(f"Starting AI server at http://{host}:{port}/ …")
    # Use threaded=True so requests don't block game thread if model is slow
    app.run(host=host, port=port, threaded=True) 