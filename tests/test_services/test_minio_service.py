import pytest
from fastapi import UploadFile
from app.services.minio_service import MinioService
from io import BytesIO
from PIL import Image
import numpy as np
from app.dependencies import get_settings
import uuid

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

@pytest.mark.asyncio
async def test_upload_invalid_image_format(settings):
    # Test uploading a file with .jpg extension but invalid image content
    invalid_file = UploadFile(
        file=BytesIO(b"Not a real JPG"),
        filename="fake.jpg",
        headers={"content-type": "image/jpeg"}
    )
    minio_service = MinioService(settings)
    with pytest.raises(Exception):
        await minio_service.upload_profile_picture(invalid_file)

@pytest.mark.asyncio
async def test_upload_oversized_image(settings):
    # Create a very large image (>5MB)
    large_img = Image.new('RGB', (3000, 3000), color='red')
    img_byte_arr = BytesIO()
    # Use uncompressed format to ensure large file size
    large_img.save(img_byte_arr, format='BMP')
    img_byte_arr.seek(0)
    
    oversized_file = UploadFile(
        file=img_byte_arr,
        filename="huge.bmp",
        headers={"content-type": "image/bmp"}
    )
    minio_service = MinioService(settings)
    with pytest.raises(Exception, match="File size exceeds maximum limit"):
        await minio_service.upload_profile_picture(oversized_file)

        
@pytest.mark.asyncio
async def test_upload_empty_file(settings):
    empty_file = UploadFile(
        file=BytesIO(b""),
        filename="empty.png",
        headers={"content-type": "image/png"}
    )
    minio_service = MinioService(settings)
    with pytest.raises(Exception, match="Empty file"):
        await minio_service.upload_profile_picture(empty_file)

@pytest.mark.asyncio
async def test_verify_image_dimensions(upload_file, settings):
    minio_service = MinioService(settings)
    url = await minio_service.upload_profile_picture(upload_file)
    
    # Get object name from URL
    object_name = url.split('/')[-1]
    
    # Download the image synchronously
    data = minio_service.client.get_object(
        minio_service.bucket_name,
        object_name
    ).read()
    
    image = Image.open(BytesIO(data))
    assert image.size == (200, 200), "Image should be resized to 200x200"

@pytest.mark.asyncio
async def test_unique_filenames(settings):
    # Create two identical images
    def create_test_image():
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return UploadFile(
            file=img_byte_arr,
            filename="test.png",
            headers={"content-type": "image/png"}
        )
    
    file1 = create_test_image()
    file2 = create_test_image()
    
    minio_service = MinioService(settings)
    url1 = await minio_service.upload_profile_picture(file1)
    url2 = await minio_service.upload_profile_picture(file2)
    
    assert url1 != url2, "Different uploads should have unique filenames"
    
@pytest.mark.asyncio
async def test_content_type_preservation(upload_file, settings):
    minio_service = MinioService(settings)
    url = await minio_service.upload_profile_picture(upload_file)
    
    # Verify the content type in Minio
    stat = minio_service.client.stat_object(
        minio_service.bucket_name,
        url.split('/')[-1]
    )
    assert stat.content_type == 'image/png'

@pytest.mark.asyncio
async def test_bucket_creation(settings):
    test_bucket_name = f"test-bucket-{uuid.uuid4()}"
    minio_service = MinioService(settings)
    original_bucket = minio_service.bucket_name
    minio_service.bucket_name = test_bucket_name
    
    try:
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        test_file = UploadFile(
            file=img_byte_arr,
            filename="test.png",
            headers={"content-type": "image/png"}
        )
        
        # Upload should create bucket if it doesn't exist
        await minio_service.upload_profile_picture(test_file)
        assert minio_service.client.bucket_exists(test_bucket_name)
    finally:
        # Clean up: restore original bucket name
        minio_service.bucket_name = original_bucket
    
@pytest.mark.asyncio
async def test_image_format_conversion(settings):
    # Create a JPEG image
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    jpeg_file = UploadFile(
        file=img_byte_arr,
        filename="test.jpg",
        headers={"content-type": "image/jpeg"}
    )
    
    minio_service = MinioService(settings)
    url = await minio_service.upload_profile_picture(jpeg_file)
    
    # Verify the image was converted to PNG
    assert url.endswith('.png'), "Image should be converted to PNG format"