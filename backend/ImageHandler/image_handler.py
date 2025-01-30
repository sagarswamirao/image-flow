import uuid
import logging
from google.cloud import storage, firestore
from flask import Flask, request, jsonify
import json
import os
import requests

current_dir = os.path.dirname(os.path.abspath(__file__))
print(current_dir)
credentials_path = os.path.join(current_dir, "dcsc-project-440602-9412462c618e.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
from datetime import timedelta
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)
GCP_PROJECT = os.getenv("GCP_PROJECT", "dcsc-project-440602")  # default for Kubernetes service
storage_client = storage.Client(project=GCP_PROJECT)
firestore_client = firestore.Client(project=GCP_PROJECT)
image_port = int(os.getenv("IMAGE_PORT", 5000))
INTERACTION_POD_URL = os.getenv("INTERACTION_POD_URL", "http://interaction-pod:8080")  # default for Kubernetes service
BATCH_TABLE_NAME=os.getenv('BATCH_TABLE_NAME','batch_uploads')
IMAGE_METADATA_TABLE_NAME=os.getenv('IMAGE_METADATA_TABLE_NAME','image_metadata')
# Configuration
BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "cu-image-flow")
logging.basicConfig(level=logging.INFO)

# Helper function to upload image to Google Cloud Storage
def upload_to_gcs(image_file, batch_uuid, image_name):
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"{batch_uuid}/input/{image_name}")
        blob.upload_from_file(image_file)
        public_url = blob.public_url
        logging.info(f"Image uploaded to GCS: {public_url}")
        return public_url
    except Exception as e:
        logging.error(f"Failed to upload image to GCS: {e}")
        raise

# Function to save data to Firestore with support for custom document IDs
def save_to_firestore(table_name, data, doc_id=None):
    try:
        doc_ref = firestore_client.collection(table_name).document(doc_id if doc_id else data["UUID"])
        doc_ref.set(data)
        logging.info(f"Data saved to Firestore: {table_name} - {data}")
    except Exception as e:
        logging.error(f"Failed to save data to Firestore: {e}")
        raise

@app.route('/get-processed-images', methods=['GET'])
def get_output_urls():
    batch_id = request.args.get('batch_id')
    if not batch_id:
        return jsonify({"error": "batch_id is required"}), 400

    try:
        input_folder = f"{batch_id}/input/"
        output_folder = f"{batch_id}/output/"

        bucket = storage_client.bucket(BUCKET_NAME)
        input_urls = {}
        output_urls = {}

        # List blobs in input folder
        for blob in bucket.list_blobs(prefix=input_folder):
            if blob.name.endswith("/"):
                continue
            file_name = os.path.basename(blob.name)
            input_urls[file_name] = blob.generate_signed_url(expiration=timedelta(hours=1))

        # List blobs in output folder
        for blob in bucket.list_blobs(prefix=output_folder):
            if blob.name.endswith("/"):
                continue
            file_name = os.path.basename(blob.name)
            output_urls[file_name] = blob.generate_signed_url(expiration=timedelta(hours=1))

        # Pair images by file name
        image_pairs = [{
            "file_name": file_name,
            "before_url": input_url,
            "after_url": output_urls[file_name]
        } for file_name, input_url in input_urls.items() if file_name in output_urls]

        if not image_pairs:
            return jsonify({"error": "No matching image pairs found for the given batch_id"}), 404

        return jsonify({"batch_id": batch_id, "image_pairs": image_pairs}), 200

    except Exception as e:
        logging.error(f"Failed to retrieve output URLs for batch_id {batch_id}: {e}")
        return jsonify({"error": f"Failed to retrieve output URLs: {e}"}), 500

@app.route('/get-images-by-status', methods=['GET'])
def get_images_by_status():
    batch_id = request.args.get('batch_id')
    is_processed = request.args.get('IsProcessed')

    if batch_id is None or is_processed is None:
        return jsonify({"error": "batch_id and IsProcessed parameters are required"}), 400

    is_processed = is_processed.lower() == 'true'

    try:
        image_metadata_ref = firestore_client.collection(IMAGE_METADATA_TABLE_NAME)
        query = image_metadata_ref.where("batch_id", "==", batch_id).where("is_processed", "==", is_processed)
        images = [doc.to_dict() for doc in query.stream()]

        if not images:
            return jsonify({"error": "No images found matching the criteria"}), 404

        return jsonify({"batch_id": batch_id, "IsProcessed": is_processed, "images": images}), 200

    except Exception as e:
        logging.error(f"Failed to retrieve images with batch_id {batch_id} and IsProcessed {is_processed}: {e}")
        return jsonify({"error": f"Failed to retrieve images: {e}"}), 500

@app.route('/upload-images', methods=['POST'])
def upload_images():
    if 'files' not in request.files or 'metadata' not in request.form:
        logging.error("Files and metadata are required")
        return jsonify({"error": "Files and metadata are required"}), 400

    files = request.files.getlist('files')
    metadata = json.loads(request.form['metadata'])
    email = metadata.get("email")
    images_metadata = metadata.get("imagesMetadata", [])

    if len(files) != len(images_metadata):
        logging.error("Number of files does not match number of metadata entries")
        return jsonify({"error": "Mismatched files and metadata entries"}), 400

    batch_uuid = str(uuid.uuid4())
    logging.info(f"Generated Batch batch_id: {batch_uuid} for the image upload")

    firestore_data_batch_uploads = {
        "email": email,
        "email_sent": False,
        "image_count": len(files),
        "job_status": "Pending"
    }
    save_to_firestore(BATCH_TABLE_NAME, firestore_data_batch_uploads, doc_id=batch_uuid)

    response_data = []
    for image_file, image_metadata in zip(files, images_metadata):
        try:
            image_name = image_metadata.get('image_name', image_file.filename)
            filters = image_metadata.get('filters', [])

            image_url = upload_to_gcs(image_file, batch_uuid, image_name)
            doc_id = f"{batch_uuid}_{image_name}"

            firestore_data_image_metadata = {
                "batch_id": batch_uuid,
                "filter_json": filters,
                "image_name": image_name,
                "is_processed": False
            }
            save_to_firestore(IMAGE_METADATA_TABLE_NAME, firestore_data_image_metadata, doc_id=doc_id)

            response_data.append({
                "image_name": image_name,
                "batch_id": batch_uuid,
                "status": "success",
                "image_url": image_url
            })

        except Exception as e:
            logging.error(f"Error processing {image_file.filename}: {e}")
            response_data.append({
                "image_name": image_name,
                "batch_id": batch_uuid,
                "status": "error"
            })

    response = requests.get(f"{INTERACTION_POD_URL}/process_batch?batch_id={batch_uuid}")
    print(f"response: {response}")
    return response.json()
    # return jsonify(response_data), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=image_port)
