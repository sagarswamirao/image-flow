from google.cloud import storage
from google.cloud import pubsub_v1
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import logging
import json
import time
from dotenv import load_dotenv
import requests
load_dotenv()
current_dir = os.path.dirname(os.path.abspath(__file__))
print(current_dir)
credentials_path = os.path.join(current_dir, "dcsc-project-440602-9412462c618e.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

# Load environment variables
PROJECT_ID = os.getenv('GCP_PROJECT', 'dcsc-project-440602')
BUCKET_NAME = os.getenv('GCP_BUCKET_NAME', 'cu-image-flow')
IMAGE_PUBSUB_TOPIC = os.getenv('IMAGE_PUBSUB_TOPIC', 'projects/dcsc-project-440602/topics/image-processing-queue')
SUBSCRIPTION_NAME = os.getenv('PUBSUB_SUBSCRIPTION', 'image-processing-queue-sub')
INTERACTION_POD_URL = os.getenv('INTERACTION_POD_URL', 'http://interaction-pod:8080')

# Initialize clients for Google Cloud services
storage_client = storage.Client()
subscriber = pubsub_v1.SubscriberClient()

logging.basicConfig(level=logging.INFO)


def callback(message):
    try:
        logging.info(f"Received message: {message.data.decode('utf-8')}")
        time.sleep(15)  # Add a delay of 15 seconds
        # logging.info("Simulated processing completed.")
        data = message.data.decode('utf-8')
        request_data = json.loads(data)

        doc_id = request_data['doc_id']
        image_name = request_data['image_name']
        filters = request_data['filters']
        # email = request_data['email']
        batch_id = request_data['batch_id']

        # Determine the file extension and MIME type
        file_extension = image_name.split('.')[-1].lower()
        logging.info(f"Processing image {image_name} with extension {file_extension}")

        # Validate the file extension
        valid_extensions = ['jpg', 'jpeg', 'png']
        if file_extension not in valid_extensions:
            logging.error(f"Error processing {image_name}: unsupported file extension {file_extension}")
            message.nack()  # Reject message and do not process unsupported image formats
            return

        # Download the image from Google Cloud Storage
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f'{batch_id}/input/{image_name}')  # Keep the extension in the path
        logging.info(f"Downloading image from GCS: {batch_id}/input/{image_name}")
        image_data = blob.download_as_bytes()

        # Apply specified filters
        logging.info(f"Applying filters: {filters}")
        processed_image = apply_filters(image_data, filters)
        logging.info(f"Processed image size: {len(processed_image)} bytes")
        # Upload the processed image to the output folder in GCS
        output_bucket = storage_client.bucket(BUCKET_NAME)
        output_blob = output_bucket.blob(f'{batch_id}/output/{image_name}')  # Keep the extension in the path
        logging.info(f"Uploading processed image to GCS: {batch_id}/output/{image_name}")
        output_blob.upload_from_file(io.BytesIO(processed_image), content_type=f'image/{file_extension}')

        # Update the status in the interaction service
        logging.info(f"Updating image status for doc_id {doc_id} and batch_id {batch_id}")
        update_image_status_to_interaction_service(doc_id, batch_id)

        message.ack()  # Acknowledge the message after successful processing
        logging.info(f"Successfully processed message for {image_name}")

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        message.nack()  # Return the message to the queue if processing fails


def apply_filters(image_data, filters):
    logging.info(f"Starting image filter application")
    # Open the image
    image = Image.open(io.BytesIO(image_data))

    # Apply each filter in sequence
    for filter_info in filters:
        filter_type = filter_info['filter_type']
        filter_value = filter_info['filter_value']

        logging.info(f"Applying filter: {filter_type} with value {filter_value}")
        if filter_type == 'rotate':
            image = image.rotate(int(filter_value))
        elif filter_type == 'grayscale':
            image = image.convert('L')
        elif filter_type == 'blur':
            image = image.filter(ImageFilter.GaussianBlur(float(filter_value)))
        elif filter_type == 'brightness':
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(float(filter_value))
        elif filter_type == 'contrast':
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(float(filter_value))
        # Add other filter types as needed

    # Save the processed image to bytes
    output_io = io.BytesIO()
    logging.info(f"image format {image.format}")
    # Ensure the processed image is saved in the correct format
    if image.format in ['JPEG', 'JPG']:
        image.save(output_io, format='JPEG')
    elif image.format == 'PNG':
        image.save(output_io, format='PNG')
    else:
        image.save(output_io, format='PNG')
        logging.error(f"Unsupported format for saving: {image.format}")
        # raise ValueError(f"Unsupported format: {image.format}")
    output_io.seek(0)
    logging.info(f"Finished applying filters")
    return output_io.getvalue()


def update_image_status_to_interaction_service(doc_id, batch_id):
    try:
        logging.info(f"Sending status update to Interaction Pod for doc_id {doc_id}, batch_id {batch_id}")
        response = requests.get(f'{INTERACTION_POD_URL}/update_image_status?doc_id={doc_id}&batch_id={batch_id}')
        response.raise_for_status()
        logging.info(f"Successfully updated image status for doc_id {doc_id} and batch_id {batch_id}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error updating status: {e}")


if __name__ == '__main__':
    # Set up a subscription path and listen for messages
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)
    logging.info(f"Listening for messages on {subscription_path}")

    # Start the subscriber to listen for messages continuously
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    # Keep the subscriber running
    try:
        streaming_pull_future.result()  # Block the main thread indefinitely
    except KeyboardInterrupt:
        streaming_pull_future.cancel()  # Stop listening if interrupted
        logging.info("Stopped listening for Pub/Sub messages.")
