import b2sdk.v2 as b2
from dotenv import load_dotenv
import os


class B2FileService:
    def __init__(self):
        load_dotenv()
        self.application_key_id = os.getenv("b2_application_key_id")
        self.application_key = os.getenv("b2_application_key")
        self.bucket_name = os.getenv("b2_bucket_name")
        self.bucket_id = os.getenv("b2_bucket_id")
        self.image_prefix = os.getenv("b2_image_prefix")

    def _get_b2_api(self):
        b2_api = b2.B2Api()
        b2_api.authorize_account("production", self.application_key_id, self.application_key)
        return b2_api
    
    def _get_download_token(self, flag):
        b2api = self._get_b2_api()
        bucket = b2.Bucket(b2api, self.bucket_id, name=self.bucket_name)
        if flag == "image":
            token = bucket.get_download_authorization(self.image_prefix, valid_duration_in_seconds=180)
        return token, b2api
    
    def get_current_file_url(self, user_id):
        token, b2_api = self._get_download_token("image")
        download_url = b2_api.account_info.get_download_url()
        return f"{download_url}/file/{self.bucket_name}/{self.image_prefix}/user_{user_id}.jpg?Authorization={token}"