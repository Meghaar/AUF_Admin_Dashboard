from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Hello from Flask!"})

@app.route('/api/data', methods=['POST'])
def get_data():
    data = request.json
    return jsonify({"you_sent": data}), 200

if __name__ == '__main__':
    app.run(debug=True)
