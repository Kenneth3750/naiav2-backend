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
        self.document_prefix = os.getenv("b2_document_prefix")

    def _get_b2_api(self):
        b2_api = b2.B2Api()
        b2_api.authorize_account("production", self.application_key_id, self.application_key)
        return b2_api
    
    def _get_download_token(self, flag):
        b2_api = self._get_b2_api()
        bucket = b2.Bucket(b2_api, self.bucket_id, name=self.bucket_name) 
        if flag == "image":
            token = bucket.get_download_authorization(self.image_prefix, valid_duration_in_seconds=604800)
        return token, b2_api
    
    def get_current_file_url(self, user_id):
        b2_api = self._get_b2_api()
        bucket = b2.Bucket(b2_api, self.bucket_id, name=self.bucket_name)
        filename = f"{self.image_prefix}/user_{user_id}.jpg"
        try:
            file_exists = False
            for file_version, _ in bucket.ls(folder_to_list=filename, recursive=False, latest_only=True):
                if file_version.file_name == filename:
                    file_exists = True
                    break
                    
            if not file_exists:
                return None
            token, b2_api = self._get_download_token("image")
            download_url = b2_api.account_info.get_download_url()
            return f"{download_url}/file/{self.bucket_name}/{filename}?Authorization={token}"
        except Exception as e:
            print(f"Error checking file existence: {str(e)}")
            return None
    
    def upload_image(self, user_id, image):
        b2_api = self._get_b2_api()
        bucket = b2.Bucket(b2_api, self.bucket_id, name=self.bucket_name)

        if hasattr(image, 'read'):
            image_data = image.read()
        else:
            image_data = image
        filename = f"{self.image_prefix}/user_{user_id}.jpg"

        try:
            # Buscamos el archivo existente
            file_versions = bucket.list_file_versions(filename)
            for file_version in file_versions:
                if file_version.file_name == filename:
                    bucket.delete_file_version(file_version.id_, filename)
                    print(f"Archivo anterior eliminado: {filename}")
                    break
        except Exception as e:
            print(f"Advertencia al intentar eliminar archivo anterior: {str(e)}")
        
        content_type = getattr(image, 'content_type', 'image/jpeg')
        
        file_info = bucket.upload_bytes(
            data_bytes=image_data,
            file_name=filename,
            content_type=content_type
        )

        return True
    

    def upload_document(self, user_id, document):
        b2_api = self._get_b2_api()
        bucket = b2.Bucket(b2_api, self.bucket_id, name=self.bucket_name)

        # list_documents = self.retrieve_all_user_documents(user_id)
        # if len(list_documents) > 5:
        #     raise Exception("User has reached the maximum number of documents (5)")
        
        if hasattr(document, 'read'):
            document_data = document.read()
        else:
            document_data = document
        filename = f"{self.document_prefix}/user_{user_id}/{document.name}"

        try:
            file_versions = bucket.list_file_versions(filename)
            for file_version in file_versions:
                if file_version.file_name == filename:
                    bucket.delete_file_version(file_version.id_, filename)
                    print(f"Archivo anterior eliminado: {filename}")
                    break
        except Exception as e:
            print(f"Advertencia al intentar eliminar archivo anterior: {str(e)}")
        
        content_type = getattr(document, 'content_type', 'application/pdf')
        
        file_info = bucket.upload_bytes(
            data_bytes=document_data,
            file_name=filename,
            content_type=content_type
        )

        serializable_info = {
            "file_id": file_info.id_,
            "file_name": file_info.file_name,
            "size": file_info.size,
            "upload_timestamp": file_info.upload_timestamp,
            "content_type": getattr(file_info, 'content_type', content_type),
        }

        return serializable_info
    
    def retrieve_all_user_documents(self, user_id):
        b2_api = self._get_b2_api()
        bucket = b2.Bucket(b2_api, self.bucket_id, name=self.bucket_name)
        prefix = f"{self.document_prefix}/user_{user_id}/"
        files = bucket.ls(folder_to_list=prefix, recursive=False)
        documents = []
        for file_info, file_metadata in files:
            full_name = file_info.file_name
            file_name = full_name.split('/')[-1]
        
            document_info = {
            "file_id": file_info.id_,
            "file_name": file_name,  
            "size": file_info.size,
            "upload_timestamp": file_info.upload_timestamp,
            "content_type": getattr(file_info, 'content_type', None),
            }
            documents.append(document_info)
        print("Retrieved from bucket")
        
        return documents
    

    def delete_document_by_id(self, file_id, file_name, user_id):
        b2_api = self._get_b2_api()
        bucket = b2.Bucket(b2_api, self.bucket_id, name=self.bucket_name)
        try:
            bucket.delete_file_version(file_id, file_name=f"{self.document_prefix}/user_{user_id}/{file_name}")
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
        
    def download_user_documents(self, user_id):
        import tempfile
        import os
        
        b2_api = self._get_b2_api()
        bucket = b2.Bucket(b2_api, self.bucket_id, name=self.bucket_name)
        prefix = f"{self.document_prefix}/user_{user_id}/"
        files = bucket.ls(folder_to_list=prefix, recursive=False)
        documents = []
        
        for file_info, file_metadata in files:
            if file_info.file_name.lower().endswith('.pdf'):
                try:
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    downloaded_file = b2_api.download_file_by_id(file_info.id_)
                    downloaded_file.save_to(temp_path)
                    
                    with open(temp_path, 'rb') as f:
                        file_bytes = f.read()
                        documents.append(file_bytes)
                    
                    os.unlink(temp_path)
                    
                    print(f"Archivo descargado: {file_info.file_name}")
                except Exception as e:
                    print(f"Error al descargar el archivo {file_info.file_name}: {str(e)}")
        
        return documents