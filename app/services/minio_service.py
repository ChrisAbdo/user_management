"""
Minio service to handle file uploads to Minio.
It provides a method to upload profile pictures to Minio. The image is resized to 200x200 pixels and saved as a PNG file.
It is then uploaded to the Minio server and the URL is returned, also setting the user's profile picture to the new URL.
"""
from minio import Minio
from fastapi import UploadFile
import io
from PIL import Image
import uuid
from settings.config import Settings

class MinioService:
    def __init__(self, settings: Settings):
        self.client = Minio(
            f"{settings.minio_host}:{settings.minio_port}",
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=False
        )
        self.bucket_name = "profile-pictures"
        self.MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    async def upload_profile_picture(self, file: UploadFile) -> str:
        try:
            # Read and validate image
            image_data = await file.read()
            
            # Check for empty file
            if not image_data:
                raise Exception("Empty file")
                
            # Check file size
            if len(image_data) > self.MAX_FILE_SIZE:
                raise Exception("File size exceeds maximum limit")
                
            image = Image.open(io.BytesIO(image_data))
            
            # Resize image to standard size
            image = image.resize((200, 200))
            
            # Convert to PNG and save to buffer
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Generate unique filename
            file_name = f"{uuid.uuid4()}.png"
            
            # Ensure bucket exists
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
            
            # Upload to Minio
            self.client.put_object(
                self.bucket_name,
                file_name,
                buffer,
                buffer.getbuffer().nbytes,
                content_type='image/png'
            )
            
            return f"http://localhost:9000/{self.bucket_name}/{file_name}"
        except Exception as e:
            print(f"Error uploading file: {e}")
            raise