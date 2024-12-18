import pytest
from fastapi import UploadFile
from app.services.minio_service import MinioService
from io import BytesIO
from PIL import Image
import numpy as np
from app.dependencies import get_settings

@pytest.fixture
def settings():
    return get_settings()

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
        file=sample_image,
        filename="test.png",
        headers={"content-type": "image/png"}
    )

@pytest.mark.asyncio
async def test_upload_profile_picture(upload_file, settings):
    minio_service = MinioService(settings)
    url = await minio_service.upload_profile_picture(upload_file)
    assert url.startswith("http://localhost:9000/profile-pictures/")
    assert url.endswith(".png")

@pytest.mark.asyncio
async def test_upload_non_image_file(settings):
    non_image_file = UploadFile(
        file=BytesIO(b"Not an image content"),
        filename="test.txt",
        headers={"content-type": "text/plain"}
    )
    minio_service = MinioService(settings)
    with pytest.raises(Exception):
        await minio_service.upload_profile_picture(non_image_file)

@pytest.mark.asyncio
async def test_upload_large_image(settings):
    # Create a large test image
    large_img = Image.fromarray(np.zeros((1000, 1000, 3), dtype=np.uint8))
    img_byte_arr = BytesIO()
    large_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    large_upload_file = UploadFile(
        file=img_byte_arr,
        filename="large_test.png",
        headers={"content-type": "image/png"}
    )
    minio_service = MinioService(settings)
    url = await minio_service.upload_profile_picture(large_upload_file)
    assert url.startswith("http://localhost:9000/profile-pictures/")
    assert url.endswith(".png")
