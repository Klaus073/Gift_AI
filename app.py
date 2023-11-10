from flask import Flask, request, jsonify, render_template
 
app = Flask(__name__)
 
# Import your code and functions here
from chatbot import main_input
 

 
@app.route('/api/main_input', methods=['POST'])
def api_main_input():
    try:
        data = request.json
 
        if 'user_input' not in data:
            # Data is missing from the request
            error_message = "Missing 'user_input' in the request data."
            return jsonify({"error": error_message , "code" :400}), 400  # 400 is the HTTP status code for Bad Request
 
        user_input = data['user_input']
       
        try:
            output = main_input(user_input)
            # print(output)
            return jsonify({"result":output})
 
        except Exception as e:
            # Handle exceptions from main_input and return an error response
            error_message = "An error occurred while processing the request: " + str(e)
            return jsonify({"error": error_message , "code":500}), 500  # 500 is the HTTP status code for Internal Server Error
 
    except Exception as e:
        # Handle exceptions related to request data and return an error response
        error_message = "An error occurred while processing the request data: "+str(e) 
        return jsonify({"error": error_message , "code":400}), 400  # 400 is the HTTP status code for Bad Request
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 4000 , debug=False)
