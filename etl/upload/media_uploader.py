import os
from typing import List, Optional
from google.cloud import storage

from utils.logger import logger
from utils.settings import PROJECT_ID, BUCKET_NAME


class MediaUploader:

    def __init__(self, client: Optional[storage.Client] = None):
        self.client = client or storage.Client(project=PROJECT_ID)
        self.bucket = self.client.bucket(BUCKET_NAME)
    
    def upload_folder(self, local_folder: str, pokemon_name: str) -> List[str]:
        if not os.path.isdir(local_folder):
            return []

        gcs_urls = []
        files_uploaded = 0

        try:
            for filename in os.listdir(local_folder):
                file_path = os.path.join(local_folder, filename)

                if not os.path.isfile(file_path):
                    continue

                blob_path = f"pokemon/{pokemon_name}/{filename}"
                blob = self.bucket.blob(blob_path)
                try:
                    blob.upload_from_filename(file_path)
                    gcs_urls.append(blob.public_url)
                    files_uploaded += 1
                    os.remove(file_path)
                except Exception:
                    pass

            try:
                if not os.listdir(local_folder):
                    os.rmdir(local_folder)
            except Exception:
                pass
        except Exception:
            pass

        return gcs_urls
