#!/usr/bin/env python3

print("Starting test app...")

from flask import Flask
print("Flask imported")

app = Flask(__name__)
print("Flask app created")

@app.route('/')
def hello():
    return "Test app is working!"

@app.route('/test')
def test():
    return "Test endpoint working!"

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5001)
