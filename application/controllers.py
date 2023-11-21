from flask import Flask, request
from flask import current_app as app

@app.route("/", methods = ["GET"])
def hello():
    return "hello"