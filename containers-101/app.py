from flask import Flask, request, jsonify
app = Flask(__name__)
todos = []

@app.route("/todos", methods=["GET"])
def list_todos():
    return jsonify(todos)

@app.route("/todos", methods=["POST"])
def add_todo():
    todos.append(request.json["task"])
    return jsonify({"result": "added"}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)