import pytest
from unittest.mock import Mock, patch
from flask import Flask
from interaction_pod import app
import json


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_firestore():
    with patch('interaction_pod.firestore_client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_publisher():
    with patch('interaction_pod.publisher') as mock_pub:
        yield mock_pub


def test_process_batch_success(client, mock_firestore, mock_publisher):
    # Mock data
    batch_id = "test-batch-123"
    test_email = "test@example.com"

    # Mock get_batch_details response
    mock_doc_dict = {'email': test_email, 'image_count': 2}
    mock_batch_doc = Mock()
    mock_batch_doc.to_dict.return_value = mock_doc_dict
    mock_batch_doc.get = lambda x: mock_doc_dict.get(x)

    mock_firestore.collection.return_value.document.return_value.get.return_value = mock_batch_doc

    # Mock image metadata response
    class MockDoc:
        def __init__(self, doc_id, data):
            self.id = doc_id
            self._data = data

        def get(self, field):
            return self._data.get(field)

        def to_dict(self):
            return self._data

    mock_metadata_docs = [
        MockDoc('doc1', {
            'image_name': 'test1.jpg',
            'batch_id': batch_id,
            'filter_json': {'brightness': 1.2}
        }),
        MockDoc('doc2', {
            'image_name': 'test2.jpg',
            'batch_id': batch_id,
            'filter_json': {'contrast': 1.5}
        })
    ]

    # Set up the chain of mock calls for the metadata query
    mock_where = Mock()
    mock_where.get.return_value = mock_metadata_docs
    mock_firestore.collection.return_value.where.return_value = mock_where

    # Mock publisher
    future = Mock()
    future.result.return_value = None
    mock_publisher.publish.return_value = future

    # Make request
    response = client.get(f'/process_batch?batch_id={batch_id}')

    # Assertions
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['status'] == 'success'
    assert response_data['message'] == 'Pushed to Pub/Sub for processing'

    # Verify publisher was called for each image
    assert mock_publisher.publish.call_count == 2


def test_update_image_status_completion(client, mock_firestore, mock_publisher):
    # Mock data
    doc_id = "test-doc-123"
    batch_id = "test-batch-456"

    # Mock no remaining unprocessed images
    mock_docs = []
    mock_query = Mock()
    mock_query.stream.return_value = mock_docs
    mock_where2 = Mock()
    mock_where2.where.return_value = mock_query
    mock_firestore.collection.return_value.where.return_value = mock_where2

    # Mock batch details for email notification
    mock_doc_dict = {
        'email': 'test@example.com',
        'image_count': 1
    }
    mock_batch_doc = Mock()
    mock_batch_doc.get = lambda x: mock_doc_dict.get(x)
    mock_firestore.collection.return_value.document.return_value.get.return_value = mock_batch_doc

    # Mock publisher
    future = Mock()
    future.result.return_value = None
    mock_publisher.publish.return_value = future

    # Make request
    response = client.get(f'/update_image_status?doc_id={doc_id}&batch_id={batch_id}')

    # Assertions
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['status'] == 'success'
    assert response_data['message'] == 'Request Completed'

    # Verify Firestore updates
    mock_firestore.collection.return_value.document.return_value.update.assert_any_call({'is_processed': True})
    mock_firestore.collection.return_value.document.return_value.update.assert_any_call({'job_status': 'Completed'})

    # Verify email notification was sent
    mock_publisher.publish.assert_called_once()