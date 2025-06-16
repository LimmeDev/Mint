from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_game_data():
    """
    Receives game data from the Captain of Industry mod,
    prints it, and returns a command.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Pretty-print the received data to the console
    print("--- Received World Data from Game ---")
    print(json.dumps(data, indent=2))
    print("------------------------------------")

    # In the future, AI logic will go here to decide on a command.
    # For now, we just send back a simple message.
    response_message = "Data received successfully. No action taken."

    return jsonify({"message": response_message})

if __name__ == '__main__':
    # Makes the server accessible from the game running on the same machine
    app.run(host='0.0.0.0', port=8000) 