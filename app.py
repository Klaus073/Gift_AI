
from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS

from chatbot import main_input
import os

app = Flask(__name__)
CORS(app)

# Route for the home page
@app.route('/')
def get_status():
    return jsonify(message="Running")

@app.route('/api/main_input', methods=['POST'])
def api_main_input():
    try:
        data = request.json

        if 'user_input' not in data and 'session_id' not in data:
            # Data is missing from the request
            error_message = "Missing 'user_input' in the request data."
            return jsonify({"error": error_message, "code": 400}), 400

        user_input = data['user_input']
        session_id = data['session_id']

        try:
            output = main_input(user_input, session_id)
            return jsonify({"result": output})

        except Exception as e:
            # Handle exceptions from main_input and return an error response
            error_message = "An error occurred while processing the request: " + str(e)
            return jsonify({"error": error_message, "code": 500}), 500

    except Exception as e:
        # Handle exceptions related to request data and return an error response
        error_message = "An error occurred while processing the request data: " + str(e)
        return jsonify({"error": error_message, "code": 400}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000, debug=True)
