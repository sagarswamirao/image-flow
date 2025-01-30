import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import json
import io
import uuid
from werkzeug.datastructures import FileStorage, MultiDict
from image_handler import app, save_to_firestore, upload_to_gcs


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_storage():
    with patch('image_handler.storage_client') as mock_storage:
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.public_url = 'https://storage.googleapis.com/fake-url'
        mock_blob.generate_signed_url.return_value = 'https://signed-url.com'
        mock_bucket.blob.return_value = mock_blob
        mock_storage.bucket.return_value = mock_bucket
        yield mock_storage


@pytest.fixture
def mock_firestore():
    with patch('image_handler.firestore_client') as mock_firestore:
        mock_doc = Mock()
        mock_doc.set = Mock()
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc

        # Mock query methods
        mock_where = Mock()
        mock_where.where.return_value = mock_where
        mock_where.stream.return_value = [
            Mock(to_dict=lambda: {
                "batch_id": "test-batch",
                "image_name": "test1.jpg",
                "is_processed": True,
                "filter_json": ["blur"]
            })
        ]
        mock_collection.where.return_value = mock_where

        mock_firestore.collection.return_value = mock_collection
        yield mock_firestore


@pytest.fixture
def mock_requests():
    with patch('image_handler.requests.get') as mock_requests:
        mock_response = Mock()
        mock_response.json.return_value = {"status": "processing"}
        mock_requests.return_value = mock_response
        yield mock_requests


def test_upload_images_success(client, mock_storage, mock_firestore, mock_requests):
    # Create test file
    test_file = (io.BytesIO(b"test image content"), "test1.jpg")

    metadata = {
        "email": "test@example.com",
        "imagesMetadata": [
            {
                "image_name": "test1.jpg",
                "filters": ["blur", "sharpen"]
            }
        ]
    }

    # Create multipart form data
    data = MultiDict([
        ('metadata', json.dumps(metadata)),
        ('files', test_file)
    ])

    # Make request
    response = client.post(
        '/upload-images',
        data=data,
        content_type='multipart/form-data'
    )

    # Assert response
    assert response.status_code == 200
    assert mock_storage.bucket.called
    assert mock_firestore.collection.called
    assert mock_requests.called


def test_get_processed_images_success(client, mock_storage):
    # Mock list_blobs to return specific results
    mock_bucket = mock_storage.bucket.return_value

    class MockBlob:
        def __init__(self, name):
            self.name = name

        def generate_signed_url(self, expiration):
            return f"https://signed-url.com/{self.name}"

    mock_bucket.list_blobs.side_effect = [
        [MockBlob("test-batch/input/test1.jpg")],
        [MockBlob("test-batch/output/test1.jpg")]
    ]

    response = client.get('/get-processed-images?batch_id=test-batch')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'image_pairs' in data


def test_get_images_by_status_success(client, mock_firestore):
    # Mock query is already set up in the fixture
    response = client.get('/get-images-by-status?batch_id=test-batch&IsProcessed=true')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'images' in data
    assert len(data['images']) == 1


def test_get_images_by_status_no_results(client, mock_firestore):
    # Override the mock to return empty results
    mock_where = mock_firestore.collection.return_value.where.return_value
    mock_where.where.return_value.stream.return_value = []

    response = client.get('/get-images-by-status?batch_id=test-batch&IsProcessed=true')

    assert response.status_code == 404
    assert b"No images found matching the criteria" in response.data


def test_save_to_firestore_success(mock_firestore):
    test_data = {
        "UUID": "test-uuid",
        "email": "test@example.com"
    }

    save_to_firestore("test_table", test_data)

    assert mock_firestore.collection.called
    mock_firestore.collection.assert_called_with("test_table")
    assert mock_firestore.collection.return_value.document.called


def test_save_to_firestore_with_custom_id(mock_firestore):
    test_data = {
        "email": "test@example.com"
    }
    custom_id = "custom-doc-id"

    save_to_firestore("test_table", test_data, doc_id=custom_id)

    assert mock_firestore.collection.called
    mock_firestore.collection.assert_called_with("test_table")
    mock_firestore.collection.return_value.document.assert_called_with(custom_id)


def test_upload_to_gcs_error(mock_storage):
    test_file = FileStorage(
        stream=io.BytesIO(b"test image content"),
        filename="test.jpg"
    )

    # Configure the mock to raise an exception
    mock_blob = mock_storage.bucket.return_value.blob.return_value
    mock_blob.upload_from_file.side_effect = Exception("Upload failed")

    with pytest.raises(Exception) as exc_info:
        upload_to_gcs(test_file, "test-batch", "test.jpg")

    assert "Upload failed" in str(exc_info.value)