import pytest
from unittest.mock import Mock, patch
from PIL import Image
import io
import json
import image_processor


@pytest.fixture
def sample_message():
    message = Mock()
    message.data = json.dumps({
        'doc_id': 'test-doc-123',
        'image_name': 'test.jpg',
        'filters': [
            {'filter_type': 'grayscale', 'filter_value': '1'},
            {'filter_type': 'blur', 'filter_value': '2.0'}
        ],
        'batch_id': 'batch-123'
    }).encode('utf-8')
    return message


@pytest.fixture
def sample_image():
    # Create a small test image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


def test_apply_filters(sample_image):
    """Test that filters are properly applied to an image"""
    filters = [
        {'filter_type': 'grayscale', 'filter_value': '1'},
        {'filter_type': 'blur', 'filter_value': '2.0'}
    ]

    # Process the image
    result = image_processor.apply_filters(sample_image, filters)

    # Verify the result
    assert isinstance(result, bytes)
    processed_image = Image.open(io.BytesIO(result))
    assert isinstance(processed_image, Image.Image)


def test_callback_unsupported_format():
    """Test handling of unsupported image formats"""
    message = Mock()
    message.data = json.dumps({
        'doc_id': 'test-doc-123',
        'image_name': 'test.gif',  # Unsupported format
        'filters': [],
        'batch_id': 'batch-123'
    }).encode('utf-8')

    # Call the callback
    image_processor.callback(message)

    # Verify the message was not acknowledged (nack'd)
    message.nack.assert_called_once()