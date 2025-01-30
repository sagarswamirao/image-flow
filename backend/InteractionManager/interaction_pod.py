from flask import Flask, request, jsonify
from google.cloud import storage, firestore
from google.cloud import pubsub_v1
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import logging
import json
from dotenv import load_dotenv
from flask_cors import CORS
current_dir = os.path.dirname(os.path.abspath(__file__))
print(current_dir)
credentials_path = os.path.join(current_dir, "dcsc-project-440602-9412462c618e.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
logging.basicConfig(level=logging.INFO)
load_dotenv()
app = Flask(__name__)
CORS(app)


# Environment variables
PROJECT_ID = os.getenv('GCP_PROJECT', 'dcsc-project-440602')
BUCKET_NAME = os.getenv('GCP_BUCKET_NAME', 'cu-image-flow')
EMAIL_PUBSUB_TOPIC = os.getenv('EMAIL_PUBSUB_TOPIC', 'projects/dcsc-project-440602/topics/email-notification-pub-sub')
IMAGE_PUBSUB_TOPIC = os.getenv('IMAGE_PUBSUB_TOPIC', 'projects/dcsc-project-440602/topics/image-processing-queue')
BATCH_TABLE_NAME=os.getenv('BATCH_TABLE_NAME','batch_uploads')
IMAGE_METADATA_TABLE_NAME=os.getenv('IMAGE_METADATA_TABLE_NAME','image_metadata')

publisher = pubsub_v1.PublisherClient()
storage_client = storage.Client(project=PROJECT_ID)
firestore_client = firestore.Client(project=PROJECT_ID)


def get_batch_details(batch_id):
    try:
        doc_ref = firestore_client.collection(BATCH_TABLE_NAME).document(batch_id)
        # Retrieve the document
        doc = doc_ref.get()

        # Check if the document exists
        if doc:
            # Access data as a dictionary
            data = doc.to_dict()
            print("Document data:", data)
            return data
        else:
            print("No such document!")

    except Exception as e:
        logging.error(f"No such document! {e}")
        # raise

def get_formatted_metadata_by_batch_id(batch_id, email):
    # Query the ImageMetadata collection for documents with the specified UUID
    docs = firestore_client.collection(IMAGE_METADATA_TABLE_NAME).where("batch_id", "==", batch_id).get()
    # Process each document into the desired format
    formatted_metadata_list = [
        {
            "doc_id": doc.id,
            "image_name": doc.get("image_name"),
            "email": email,
            "batch_id": doc.get("batch_id"),
            "filters": doc.get("filter_json")
        }
        for doc in docs
    ]
    
    # Check if there are any documents and return formatted list
    if formatted_metadata_list:
        print("Formatted Metadata List:", formatted_metadata_list)
    else:
        print("No documents found for the specified UUID.")

    return formatted_metadata_list

def mark_image_as_processed(doc_id):
    obj = firestore_client.collection(IMAGE_METADATA_TABLE_NAME).document(doc_id)
    obj.update({'is_processed': True})

def check_if_all_images_in_the_batch_are_processed(batch_id):
    query = firestore_client.collection(IMAGE_METADATA_TABLE_NAME).where('batch_id', '==', batch_id).where('is_processed', '==', False)
    docs = query.stream()
    count = sum(1 for _ in docs)
    return True if count==0 else False

def update_batch_status_to_completed(batch_id):
    obj = firestore_client.collection(BATCH_TABLE_NAME).document(batch_id)
    obj.update({'job_status': "Completed"})

def push_to_image_pub_sub(message_data):
    try:        
        # Serialize the message to JSON format
        data = json.dumps(message_data).encode('utf-8')
        
        # Publish the message to Pub/Sub
        future = publisher.publish(IMAGE_PUBSUB_TOPIC, data)
        future.result()  # Block until the message is published
        print("Pushed to Image Processing Pub/Sub")
        logging.info("Pushed to Image Processing Pub/Sub")
        
    except Exception as e:
        print(str(e))
        logging.error(str(e))  # Use error logging for exceptions
        # return jsonify({'status': 'error', 'message': str(e)}), 500

def push_to_email_notification_pub_sub(batch_id):
    try:
        batch_ref = firestore_client.collection(BATCH_TABLE_NAME).document(batch_id)
        batch_obj= batch_ref.get()

        message_data = {
            "batch_id": batch_id,
            "email": batch_obj.get('email'),
            "image_count": batch_obj.get('image_count')
        }
        
        # Serialize the message to JSON format
        data = json.dumps(message_data).encode('utf-8')
        
        # Publish the message to Pub/Sub
        future = publisher.publish(EMAIL_PUBSUB_TOPIC, data)
        future.result()  # Block until the message is published
        print("Pushed to Email Notification Pub/Sub")
        logging.debug("Pushed to Email Notification Pub/Sub")
        return jsonify({'status': 'success', 'message': 'Pushed to Email Notification Pub/Sub'}), 200
    except Exception as e:
        print(str(e))
        logging.error(str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

# DONE
@app.route('/process_batch', methods=['GET'])
def process_batch():
    logging.info("coming to process images")
    client_ip = request.remote_addr
    logging.debug(f"Received request from IP: {client_ip}")
    try:
        batch_id = request.args.get('batch_id')
        logging.info(f"processing for batch: {batch_id} for the image upload")
        batch_obj=get_batch_details(batch_id)
        email = batch_obj['email']
        image_data_list = get_formatted_metadata_by_batch_id(batch_id, email)
        logging.info(f"after metadata: {image_data_list}")
        for image_data in image_data_list:
            push_to_image_pub_sub(image_data)

        doc_ref = firestore_client.collection(BATCH_TABLE_NAME).document(batch_id)
        doc_ref.update({"job_status": 'In Progress'})  
        return jsonify({'status': 'success', 'message': 'Pushed to Pub/Sub for processing'}), 200
    except Exception as e:
        print(str(e))
        logging.error(str(e))  # Use error logging for exceptions
        return jsonify({'status': 'error', 'message': str(e)}), 500


# DONE
@app.route('/update_image_status', methods=['GET'])
def update_image_status():
    client_ip = request.remote_addr
    logging.info(f"Received request from IP: {client_ip}")
    try:
        image_doc_id = request.args.get('doc_id')
        batch_id= request.args.get('batch_id')

        mark_image_as_processed(image_doc_id)
        if check_if_all_images_in_the_batch_are_processed(batch_id):
            update_batch_status_to_completed(batch_id)
            push_to_email_notification_pub_sub(batch_id)
        
        return jsonify({'status': 'success', 'message': 'Request Completed'}), 200
    except Exception as e:
        print(str(e))
        logging.error(str(e))  # Use error logging for exceptions
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
