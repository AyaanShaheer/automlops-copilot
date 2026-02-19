import os
import boto3
from botocore.exceptions import ClientError
from loguru import logger
from pathlib import Path


class S3Manager:
    """Manages uploads to DigitalOcean Spaces (S3-compatible)"""

    def __init__(
        self,
        access_key: str = None,
        secret_key: str = None,
        endpoint: str = "nyc3.digitaloceanspaces.com",
        region: str = "nyc3",
        bucket: str = "automlops-models",
    ):
        self.access_key = (access_key or os.getenv("DO_SPACES_KEY", "")).strip()
        self.secret_key = (secret_key or os.getenv("DO_SPACES_SECRET", "")).strip()
        self.endpoint = endpoint
        self.region = region
        self.bucket = bucket

        if not self.access_key or not self.secret_key:
            logger.warning("S3 credentials not configured - upload features disabled")
            self.enabled = False
            return

        self.enabled = True

        # Initialize S3 client
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"https://{self.endpoint}",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )

        logger.info(f"S3Manager initialized for bucket: {self.bucket}")

    def upload_file(self, local_path: str, s3_key: str):
        """Upload a single file to S3"""

        if not self.enabled:
            logger.warning("S3 not configured - skipping upload")
            return False

        try:
            logger.info(f"Uploading {local_path} to s3://{self.bucket}/{s3_key}")

            self.s3_client.upload_file(
                local_path, self.bucket, s3_key, ExtraArgs={"ACL": "private"}
            )

            logger.success(f"File uploaded: s3://{self.bucket}/{s3_key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            return False

    def upload_directory(self, local_dir: str, s3_prefix: str):
        """Upload entire directory to S3"""

        if not self.enabled:
            logger.warning("S3 not configured - skipping upload")
            return False

        local_path = Path(local_dir)

        if not local_path.exists() or not local_path.is_dir():
            logger.error(f"Directory not found: {local_dir}")
            return False

        uploaded_files = []

        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                # Calculate relative path
                relative_path = file_path.relative_to(local_path)
                s3_key = f"{s3_prefix}/{relative_path}".replace("\\", "/")

                if self.upload_file(str(file_path), s3_key):
                    uploaded_files.append(s3_key)

        logger.success(
            f"Uploaded {len(uploaded_files)} files to s3://{self.bucket}/{s3_prefix}"
        )
        return len(uploaded_files) > 0

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600):
        """Generate a presigned URL for downloading a file"""

        if not self.enabled:
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=expiration,
            )

            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    def list_files(self, prefix: str):
        """List files in S3 with given prefix"""

        if not self.enabled:
            return []

        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)

            files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    files.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"],
                        }
                    )

            return files

        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def delete_file(self, s3_key: str):
        """Delete a file from S3"""

        if not self.enabled:
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)

            logger.info(f"Deleted: s3://{self.bucket}/{s3_key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False
