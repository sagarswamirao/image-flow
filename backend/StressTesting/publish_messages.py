import os
from google.cloud import pubsub_v1
import json

# Replace with your project ID and topic name
PROJECT_ID = "dcsc-project-440602"  # Replace with your GCP project ID
TOPIC_NAME = "image-processing-queue"  # Replace with your Pub/Sub topic name
current_dir = os.path.dirname(os.path.abspath(__file__))

# Path to your service account key
credentials_path = os.path.join(current_dir, "dcsc-project-440602-9412462c618e.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

def publish_messages():
    # Initialize Pub/Sub publisher client
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

    # Generate 1000 test messages dynamically
    messages = []
    for i in range(1000): 
        message = {
            "doc_id": str(i+1),
            "image_name": f"test_image_{i+1}.jpg",
            "filters": [{"filter_type": "rotate", "filter_value": "45"}],
            "batch_id": f"batch_{i+1}"
        }
        messages.append(message)

    # Publish each message
    for message in messages:
        # Convert message to JSON string
        message_json = json.dumps(message).encode("utf-8")
        # Publish the message
        future = publisher.publish(topic_path, data=message_json)
        print(f"Published message ID: {future.result()}")

if __name__ == "__main__":
    publish_messages()
