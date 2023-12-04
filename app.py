
from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
import logging
from chatbot import main_input , delete_memory_for_session
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__)
CORS(app)
key_times = {}
# log_file_path = 'app_log.txt'
# logging.basicConfig(filename=log_file_path, level=logging.DEBUG)

# Route for the home page
@app.route('/')
def get_status():
    return jsonify(message="Running")

def assign_time_to_key(key):
    if key not in key_times:
        key_times[key] = datetime.now()
        print(f"Key '{key}' assigned time: {key_times[key]}")

def check_keys():
    global key_times
    # print("cron jab was here",datetime.now() )
    current_time = datetime.now()
    
    try:
        for key, assigned_time in list(key_times.items()):
            if current_time - assigned_time > timedelta(days=1):
                print("time over for key:", key)
                delete_memory_for_session(key)
                del key_times[key]
    except Exception as e:
        print(f"Error in check_keys: {e}")


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
        assign_time_to_key(session_id)

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
    
@app.route('/api/delete_memory_for_session', methods=['POST'])
def delete_key_route():
    data = request.get_json()
    key_to_delete = data.get('session_id')

    if key_to_delete is None:
        return jsonify({'status': 'error', 'message': 'Key to delete not provided in the request.'})

    result = delete_memory_for_session( key_to_delete)
    return result 

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_keys, trigger='interval', days=1)
    scheduler.start()
    app.run(host='0.0.0.0', port=4000, debug=True)
