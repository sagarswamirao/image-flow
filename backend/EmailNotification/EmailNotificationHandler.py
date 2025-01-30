import base64
import json
import functions_framework
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
DOMAIN_NAME = os.getenv('DOMAIN_NAME', 'http://localhost:3000')


@functions_framework.http
def pubsub_to_email(request):
    print("Received request:", request.get_data(as_text=True))

    if request.method != 'POST':
        return 'Only POST requests are accepted', 405

    try:
        # Parse and validate the Pub/Sub message
        request_json = request.get_json()
        print("JSON request:", request_json)

        if not request_json or 'message' not in request_json:
            print("Invalid request format:", request_json)
            return 'Invalid request format', 400

        # Extract and decode the Pub/Sub message data
        pubsub_message = request_json['message']
        message_data = pubsub_message.get('data')

        if message_data:
            decoded_data = base64.b64decode(message_data).decode('utf-8')
            print("Decoded message data:", decoded_data)

            # Parse the JSON data from the decoded message
            message_json = json.loads(decoded_data)
            batch_id = message_json.get('batch_id')
            email = message_json.get('email')
            image_count = message_json.get('image_count')

            if not batch_id or not email:
                print("Missing batch_id or email in message:", message_json)
                return 'Invalid message format', 400

            # Prepare the email content
            subject = f"Your Batch ID: {batch_id}"
            body = (
                f"Hello,\n\nYour images have been processed. "
                f"You can view them by entering the batch ID: {batch_id} under the 'Processed Images' tab.\n"
                f"Alternatively, you can click the link below to directly access your gallery:\n"
                f"{DOMAIN_NAME}/#/processed/{batch_id}\n\n"
                "Thank you for using our service!"
            )

            # Send the email
            send_email(email, subject, body)
            print(f"Email sent to {email} with batch ID {batch_id}")

            return f'Notification sent to {email} for batch ID: {batch_id}', 200
        else:
            print("No data found in message")
            return 'No data found in message', 400

    except Exception as e:
        print("Error processing request:", str(e))
        return f'Error processing request: {str(e)}', 500


def send_email(to_email, subject, body):
    try:
        # Create email message
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email

        # Connect to the SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Enable TLS for security
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to_email, msg.as_string())

        print("Email sent successfully")
    except Exception as e:
        print("Error sending email:", str(e))
        raise
