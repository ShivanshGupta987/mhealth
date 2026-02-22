import os
import logging
from minio import Minio
from minio.error import S3Error
from app.config import (MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
BUCKET_NAME = "recordings"
# ---------------------

def get_recordings():
    """Connects to MinIO and lists all recordings in the bucket."""
    client = None
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False # Set to True if using HTTPS
        )

        logger.info("------- Connected to MinIO --------")

        if not client.bucket_exists(BUCKET_NAME):
            logger.warning(f"Bucket '{BUCKET_NAME}' does not exist.")
            return []

        # List all objects in the bucket
        objects = client.list_objects(BUCKET_NAME, recursive=True)
        blob_list = [obj.object_name for obj in objects]

        if not blob_list:
            logger.info(f"No recordings found in the bucket '{BUCKET_NAME}'.")
            return []

        logger.info(f"Found {len(blob_list)} recordings:")
        for blob_name in blob_list:
            logger.info(f"- {blob_name}")

        return blob_list

    except S3Error as e:
        logger.error(f"MinIO client error: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to connect to MinIO or list objects: {str(e)}")
        return []


def download_recording(object_name, local_file_path):
    """Downloads a specific object from MinIO to a local file."""
    client = None
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )

        logger.info(f"---------- Downloading '{object_name}' to '{local_file_path}' ---------")

        client.fget_object(BUCKET_NAME, object_name, local_file_path)
        
        logger.info("------- Download complete! --------")
        return True
        
    except S3Error as e:
        logger.error(f"Failed to download recording '{object_name}': {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during download: {str(e)}")
        return False


if __name__ == "__main__":
    recordings = get_recordings()

    # if recordings:
    #     download_dir = "downloaded_recordings"
    #     if not os.path.exists(download_dir):
    #         os.makedirs(download_dir)
    #         logger.info(f"Created directory: {download_dir}")

    #     for filename in recordings:
    #         local_path = os.path.join(download_dir, filename)
    #         download_recording(filename, local_path)
            
    print("\nAll recordings have been shown.")