#!/usr/bin/env python3
"""Upload rendered videos to Google Drive via service account.

Reads the shared folder ID from state/batch_queue.json.
Uses a service account JSON key from scripts/service-account-key.json.
"""

import argparse, json, os, sys

SCOPES = ['https://www.googleapis.com/auth/drive.file']
STATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'state', 'batch_queue.json')
KEY_PATH = os.path.join(os.path.dirname(__file__), 'service-account-key.json')


def get_drive_service():
    """Prefer the OAuth refresh token (real user quota), fall back to a key file.

    A bare service account has no Drive storage quota of its own, so uploads
    fail with "Service Accounts do not have storage quota" unless the file
    lands in a Shared Drive. The OAuth path uploads as the real account, which
    does have quota.
    """
    from googleapiclient.discovery import build

    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN")

    if client_id and client_secret and refresh_token:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        credentials.refresh(Request())
        return build('drive', 'v3', credentials=credentials)

    from google.oauth2 import service_account
    if not os.path.exists(KEY_PATH):
        print(f"ERROR: no credentials. Set GOOGLE_OAUTH_CLIENT_ID / "
              f"GOOGLE_OAUTH_CLIENT_SECRET / GOOGLE_OAUTH_REFRESH_TOKEN, "
              f"or place a key file at {KEY_PATH}")
        sys.exit(1)

    credentials = service_account.Credentials.from_service_account_file(
        KEY_PATH, scopes=SCOPES)
    return build('drive', 'v3', credentials=credentials)


def get_folder_id():
    # An environment variable wins, so CI can supply the folder id without
    # it having to live in this repo.
    folder_id = os.environ.get("COGNISTRATION_SHORTS_DRIVE_FOLDER_ID")
    if not folder_id:
        with open(STATE_PATH) as f:
            state = json.load(f)
        folder_id = state.get('driveFolderId')
    if not folder_id or folder_id == 'REPLACE_WITH_YOUR_DRIVE_FOLDER_ID':
        print("ERROR: driveFolderId not set. Set COGNISTRATION_SHORTS_DRIVE_FOLDER_ID "
              "or fill in state/batch_queue.json")
        sys.exit(1)
    return folder_id


def upload(file_path: str, batch_id: str, brain_state: str, cleanup: bool = False):
    """Upload a video to the shared Drive folder."""
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    file_name = os.path.basename(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    folder_id = get_folder_id()

    print(f"Uploading: {file_name} ({file_size_mb:.1f} MB)")
    print(f"  Brain state: {brain_state}")
    print(f"  Batch ID:    {batch_id}")
    print(f"  Folder ID:   {folder_id}")

    service = get_drive_service()

    file_metadata = {
        'name': file_name,
        'parents': [folder_id],
        'description': f'Cognistration Short — {brain_state} — batch {batch_id}',
        'appProperties': {
            'brainState': brain_state,
            'batchId': batch_id,
        },
    }

    media = service.files().create(
        body=file_metadata,
        media_body=file_path,
        fields='id, name, webViewLink',
    ).execute()

    file_id = media.get('id')
    print(f"\nUpload complete!")
    print(f"  File ID:      {file_id}")
    print(f"  Name:         {media.get('name')}")
    print(f"  Web link:     {media.get('webViewLink')}")

    if cleanup:
        os.remove(file_path)
        print(f"  Cleaned up local file: {file_path}")

    return file_id


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upload video to Google Drive')
    parser.add_argument('file_path', help='Path to the MP4 file')
    parser.add_argument('--id', required=True, dest='batch_id',
                        help='Batch ID from the queue')
    parser.add_argument('--state', required=True, dest='brain_state',
                        help='Brain state (theta, alpha, delta, etc.)')
    parser.add_argument('--cleanup', action='store_true',
                        help='Delete local file after successful upload')
    args = parser.parse_args()

    upload(args.file_path, args.batch_id, args.brain_state, args.cleanup)