"""Cloudinary helper for PDF storage"""
import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def upload_pdf(file_path: str, public_id: str = None) -> dict:
    """Upload PDF to Cloudinary"""
    result = cloudinary.uploader.upload(
        file_path,
        resource_type="raw",
        public_id=public_id,
        folder="protocols"
    )
    return {
        "url": result['secure_url'],
        "public_id": result['public_id']
    }

def upload_pdf_bytes(pdf_bytes: bytes, public_id: str) -> dict:
    """Upload PDF bytes to Cloudinary"""
    result = cloudinary.uploader.upload(
        pdf_bytes,
        resource_type="raw",
        public_id=public_id,
        folder="protocols"
    )
    return {
        "url": result['secure_url'],
        "public_id": result['public_id']
    }

def delete_pdf(public_id: str) -> bool:
    """Delete PDF from Cloudinary"""
    result = cloudinary.uploader.destroy(public_id, resource_type="raw")
    return result.get('result') == 'ok'

def get_pdf_url(public_id: str) -> str:
    """Get PDF URL from Cloudinary"""
    return cloudinary.CloudinaryResource(public_id, resource_type="raw").url
