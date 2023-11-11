from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
import secrets
 
app = Flask(__name__)
 
# Replace 'your_secret_key' with a strong secret key for session encryption
app.config['SECRET_KEY'] = 'your_secret_key'
 
# Configure session to use server-side sessions (you can use other session storage options)
app.config['SESSION_TYPE'] = 'filesystem'
 
# Set a unique name for the session cookie
app.config['SESSION_COOKIE_NAME'] = 'unique_session_cookie_name'
 
# Initialize Flask-Session
Session(app)
 
# Import your code and functions here
from chatbot_db import ConversationManager
import os
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/api/main_input', methods=['POST'])
def api_main_input():
    api_key = os.environ.get("OPENAI_API_KEY")
    manager = ConversationManager(api_key)
    try:
        data = request.json
 
        if 'user_input' not in data:
            # Data is missing from the request
            error_message = "Missing 'user_input' in the request data."
            return jsonify({"error": error_message, "code": 400}), 400  # 400 is the HTTP status code for Bad Request
 
        user_input = data['user_input']
 
        # Use the user's session ID as a key for their chat data
        user_session_id = session.get('user_session_id')
        if user_session_id is None:
            user_session_id = secrets.token_hex(16)  # Generate a 32-character random hexadecimal string
            session['user_session_id'] = user_session_id
 
        try:
            # Retrieve or initialize the user's chat data
            user_chat_data = session.get(f'user_chat_data_{user_session_id}', [])
 
            # Process the user input using your chatbot
            output = manager.main_input(user_input)
 
            # Update the user's chat data
            user_chat_data.append({"input": user_input, "output": output})
            session[f'user_chat_data_{user_session_id}'] = user_chat_data
 
            return jsonify({"result": output, "user_chat_data": user_chat_data})
 
        except Exception as e:
            # Handle exceptions from main_input and return an error response
            error_message = "An error occurred while processing the request: " + str(e)
            return jsonify({"error": error_message, "code": 500}), 500  # 500 is the HTTP status code for Internal Server Error
 
    except Exception as e:
        # Handle exceptions related to request data and return an error response
        error_message = "An error occurred while processing the request data: " + str(e)
        return jsonify({"error": error_message, "code": 400}), 400  # 400 is the HTTP status code for Bad Request
 
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000, debug=True)
 