import pytest
from fastapi import UploadFile
from app.services.minio_service import MinioService
from io import BytesIO
from PIL import Image
import numpy as np

@pytest.fixture
def sample_image():
    # Create a small test image
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@pytest.fixture
def upload_file(sample_image):
    return UploadFile(
        filename="test.png",
        file=sample_image,
        content_type="image/png"
    )

@pytest.mark.asyncio
async def test_upload_profile_picture(upload_file, settings):
    minio_service = MinioService(settings)
    url = await minio_service.upload_profile_picture(upload_file)
    assert url.startswith("http://localhost:9000/profile-pictures/")
    assert url.endswith(".png")