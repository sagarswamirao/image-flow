import json
from flask import Flask, request

# Import your Cloud Function
from EmailNotificationHandler import pubsub_to_email

app = Flask(__name__)

@app.route("/test", methods=["POST"])
def test_pubsub_to_email():
    return pubsub_to_email(request)

if __name__ == "__main__":
    app.run(port=8080)
