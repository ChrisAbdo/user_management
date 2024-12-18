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
    img_byte_arr = BytesIO()
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

@pytest.mark.asyncio
async def test_image_resizing(settings, large_upload_file):
    # Initialize MinioService
    minio_service = MinioService(settings)
    
    # Upload the large image
    url = await minio_service.upload_profile_picture(large_upload_file)
    
    # Download the image from the returned URL to verify its size
    response = await httpx.get(url)
    image_data = io.BytesIO(response.content)
    image = Image.open(image_data)
    
    # Check if the image was resized to 200x200
    assert image.size == (200, 200), "Image should be resized to 200x200"