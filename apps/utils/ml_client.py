"""
ML Service Client for FastAPI Classification Service.
"""
import os
import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MLServiceClient:
    """Client for interacting with FastAPI ML Classification Service."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv('ML_SERVICE_URL', 'http://localhost:8001')
        self.timeout = int(os.getenv('ML_SERVICE_TIMEOUT', '30'))
        logger.info(f"ML Service Client initialized with base_url: {self.base_url}")

    def health_check(self) -> bool:
        """Check if ML service is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ML service health check failed: {e}")
            return False

    def classify_image(self, image_path: str, mime_type: str = 'image/jpeg') -> Dict:
        """
        Classify an image using ML service. Returns:
        {
            'kategori_sampah': str (organik|anorganik|residu|tidak_dikenal),
            'confidence_score': float,
            'is_recyclable': bool,
            'handling_instructions': str,
        }
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            classify_url = f"{self.base_url}/classify"
            with open(image_path, 'rb') as img_file:
                files = {'file': (os.path.basename(image_path), img_file, mime_type)}
                response = requests.post(classify_url, files=files, timeout=self.timeout)
                response.raise_for_status()

                result = response.json()
                if not result.get('success'):
                    raise ValueError(f"ML service returned error: {result}")

                return result.get('data', {})
        except requests.RequestException as e:
            logger.error(f"ML service request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during classification: {e}")
            raise
