from flask import Flask, request, jsonify
import requests
import json

# Create a Flask web server
app = Flask(__name__)

# The IP address of your Windows PC running Ollama
# Make sure Ollama is running and accessible.
OLLAMA_HOST = "192.168.68.64" 
OLLAMA_PORT = 11434
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"

def get_ai_decision(game_state_json):
    """
    Sends the game state to the local LLM and gets a decision.
    """
    # This is the prompt that shapes the AI's thinking.
    # We can make this much more complex later.
    prompt = f"""
    You are a Factorio engineer AI. Your goal is to automate the production of red and green science packs.
    You are given your current status as a JSON object.
    
    Current status:
    {game_state_json}

    Based on this status, what is the single, most logical next action to take?
    Be concise and clear. Your response will be used as a thought process for the next action.
    Example responses:
    - "My inventory is empty. I need to mine some iron ore."
    - "I have enough resources. I should craft a stone furnace."
    - "There are no trees nearby. I need to find a forest to get wood."
    """
    
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False  # We want the full response at once
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        response_data = response.json()
        ai_thought = response_data.get("response", "AI model did not provide a response.").strip()
        
        print(f"AI Decision: {ai_thought}")
        return ai_thought

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama: {e}")
        return f"Error: Could not connect to the AI brain at {OLLAMA_URL}."
    except json.JSONDecodeError:
        print(f"Error decoding JSON from Ollama. Response was: {response.text}")
        return "Error: Could not understand the AI's response."

# Define a route that listens for POST requests at the /' endpoint
@app.route('/', methods=['POST'])
def handle_game_data():
    # Get the JSON data sent from the Factorio mod
    game_data = request.json
    
    # Print the received data to the console (for debugging)
    print("Received data from Factorio:")
    print(json.dumps(game_data, indent=2))
    
    # Get a decision from the AI
    ai_decision_text = get_ai_decision(json.dumps(game_data))
    
    # Send the AI's thought process back to the game
    response_command = {
        "command": "thought",
        "text": ai_decision_text
    }
    
    return jsonify(response_command)

if __name__ == '__main__':
    # Run the server on host 0.0.0.0 to make it accessible
    # on your local network, and use port 8000.
    app.run(host='0.0.0.0', port=8000)
