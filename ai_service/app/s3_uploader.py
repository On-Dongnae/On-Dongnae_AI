import os
import boto3
import logging
from botocore.exceptions import NoCredentialsError, ClientError

logger = logging.getLogger(__name__)

AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-2")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")

def get_s3_client():
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        logger.warning("[S3] AWS credentials are not set in environment variables.")
        return None
        
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

def upload_image_to_s3(file_bytes: bytes, file_name: str, content_type: str = "image/jpeg") -> str:
    """
    Uploads an image to S3 and returns the public URL.
    """
    s3_client = get_s3_client()
    if not s3_client:
        raise Exception("S3 Client could not be initialized.")

    if not S3_BUCKET_NAME:
        raise Exception("S3_BUCKET_NAME is not set in environment variables.")

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_name,
            Body=file_bytes,
            ContentType=content_type,
            # If ACL public-read is needed, AWS bucket needs to allow it.
            # ACL='public-read' 
        )
        
        url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file_name}"
        logger.info(f"[S3] Successfully uploaded {file_name} to {url}")
        return url
        
    except NoCredentialsError:
        logger.error("[S3] Credentials not available.")
        raise
    except ClientError as e:
        logger.error(f"[S3] Upload failed: {e}")
        raise
