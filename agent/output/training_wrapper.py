import logging
import os
import pickle
import sys
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load original training code
try:
    from train import train_model
except ImportError as e:
    logger.error(f"Failed to import original training code: {e}")
    sys.exit(1)

def save_model(model, model_path):
    """Save the trained model to a local file"""
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved to {model_path}")
    except Exception as e:
        logger.error(f"Failed to save model: {e}")

def upload_model_to_s3(model_path, bucket_name, object_name):
    """Upload the model to S3 (DO Spaces)"""
    try:
        s3 = boto3.client('s3', aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                          aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
        s3.upload_file(model_path, bucket_name, object_name)
        logger.info(f"Model uploaded to {bucket_name}/{object_name}")
    except NoCredentialsError:
        logger.error("Credentials not available")
    except Exception as e:
        logger.error(f"Failed to upload model: {e}")

def train_and_save_model(model_path, bucket_name, object_name):
    """Train the model, save it locally, and upload it to S3"""
    try:
        model, X_test, y_test = train_model()
        y_pred = model.predict(X_test)
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'classification_report': classification_report(y_test, y_pred),
            'confusion_matrix': confusion_matrix(y_test, y_pred)
        }
        logger.info(f"Training metrics: {metrics}")
        save_model(model, model_path)
        upload_model_to_s3(model_path, bucket_name, object_name)
        return metrics
    except Exception as e:
        logger.error(f"Failed to train and save model: {e}")
        return None

if __name__ == "__main__":
    model_path = "model.pkl"
    bucket_name = os.environ['BUCKET_NAME']
    object_name = f"model-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.pkl"
    metrics = train_and_save_model(model_path, bucket_name, object_name)
    if metrics:
        logger.info("Training completed successfully")
    else:
        logger.error("Training failed")