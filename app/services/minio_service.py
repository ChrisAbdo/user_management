from minio import Minio
from fastapi import UploadFile
import io
from PIL import Image
import uuid
from config import Settings

class MinioService:
    def __init__(self, settings: Settings):
        self.client = Minio(
            f"{settings.minio_host}:{settings.minio_port}",
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=False
        )
        self.bucket_name = "profile-pictures"

    async def upload_profile_picture(self, file: UploadFile) -> str:
        try:
            # Read and validate image
            image_data = await file.read()
            image = Image.open(io.BytesIO(image_data))
            
            # Resize image to standard size
            image = image.resize((200, 200))
            
            # Convert to PNG and save to buffer
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Generate unique filename
            file_name = f"{uuid.uuid4()}.png"
            
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