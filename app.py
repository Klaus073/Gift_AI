from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Import your code and functions here
from chatbot import main_input

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/main_input', methods=['POST'])
def api_main_input():
    data = request.json
    user_input = data['user_input']
    
    result = main_input(user_input)

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
