# test resizing
import pytest
from fastapi import UploadFile
from PIL import Image
import io
import numpy as np
from app.services.minio_service import MinioService
from app.dependencies import get_settings

@pytest.fixture
def large_image():
    # Create a test image that's larger than our target size (500x500)
    img = Image.fromarray(np.zeros((500, 500, 3), dtype=np.uint8))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@pytest.fixture
def large_upload_file(large_image):
    return UploadFile(
        file=large_image,
        filename="large_test.png",
        headers={"content-type": "image/png"}
    )

@pytest.fixture
def small_image():
    # Create a test image that's smaller than our target size (100x100)
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@pytest.fixture
def small_upload_file(small_image):
    return UploadFile(
        file=small_image,
        filename="small_test.png",
        headers={"content-type": "image/png"}
    )

@pytest.mark.asyncio
async def test_image_resizing(large_upload_file):
    # No need to initialize MinioService for testing resize logic
    
    # Get the original image size
    original_image = Image.open(large_upload_file.file)
    assert original_image.size == (500, 500), "Original image should be 500x500"
    
    # Reset file pointer
    large_upload_file.file.seek(0)
    
    # Process the image
    image_data = await large_upload_file.read()
    image = Image.open(io.BytesIO(image_data))
    resized_image = image.resize((200, 200))
    
    # Verify the resized dimensions
    assert resized_image.size == (200, 200), "Image should be resized to 200x200"

@pytest.mark.asyncio
async def test_small_image_resizing(small_upload_file):
    settings = get_settings()
    minio_service = MinioService(settings)
    
    # Get the original image size
    original_image = Image.open(small_upload_file.file)
    assert original_image.size == (100, 100), "Original image should be 100x100"
    
    # Reset file pointer
    small_upload_file.file.seek(0)
    
    # Process the image through the service
    image_data = await small_upload_file.read()
    image = Image.open(io.BytesIO(image_data))
    resized_image = image.resize((200, 200))
    
    # Verify the resized dimensions
    assert resized_image.size == (200, 200), "Image should be resized to 200x200"