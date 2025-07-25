import os
import mimetypes
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from oauth2client.service_account import ServiceAccountCredentials
import io

SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = '150im9AGZ00so76tCmjMWiHPHyCQEZxgn'  # ← ID твоєї папки на Google Диску

def download_media_from_drive(credentials_path='telegrambot-466822-28f26bb10553.json'):
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, SCOPES)
    service = build('drive', 'v3', credentials=creds)

    results = service.files().list(q=f"'{FOLDER_ID}' in parents and trashed=false",
                                   fields="files(id, name, mimeType)").execute()
    items = results.get('files', [])

    os.makedirs("photos", exist_ok=True)
    downloaded_files = []

    for item in items:
        file_id = item['id']
        file_name = item['name']
        mime_type = item['mimeType']

        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(os.path.join("photos", file_name), 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        downloaded_files.append(os.path.join("photos", file_name))

    return downloaded_files
