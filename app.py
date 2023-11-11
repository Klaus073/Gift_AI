# app.py

from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from session_utils import init_session, get_user_session_id
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'unique_session_cookie_name'
Session(app)

# Import other necessary modules and libraries

from chatbot import main_input
import os

# Initialize ConversationManager
api_key = os.environ.get("OPENAI_API_KEY")
# manager = ConversationManager(api_key)

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint for handling user inputs
@app.route('/api/main_input', methods=['POST'])
def api_main_input():
    try:
        data = request.json

        if 'user_input' not in data:
            # Data is missing from the request
            error_message = "Missing 'user_input' in the request data."
            return jsonify({"error": error_message, "code": 400}), 400

        user_input = data['user_input']

        # Use the user's session ID as a key for their chat data
        init_session()
        user_session_id = get_user_session_id()
        

        try:
            # Retrieve or initialize the user's chat data
            # user_chat_data = session.get(f'user_chat_data_{user_session_id}', [])

            # Process the user input using your chatbot
            # output = manager.main_input(user_input, user_session_id)
            # print("sdfs",user_session_id)
            output = main_input(user_input, user_session_id)

            # Update the user's chat data
            # user_chat_data.append({"input": user_input, "output": output})
            # session[f'user_chat_data_{user_session_id}'] = user_chat_data

            return jsonify({"result": output })

        except Exception as e:
            # Handle exceptions from main_input and return an error response
            error_message = "An error occurred while processing the request: " 
            return jsonify({"error": error_message, "code": 500}), 500

    except Exception as e:
        # Handle exceptions related to request data and return an error response
        error_message = "An error occurred while processing the request data: " 
        return jsonify({"error": error_message, "code": 400}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000, debug=True)
