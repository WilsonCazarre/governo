import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main():

    # Call the Drive v3 API
    results = (
        service.files()
        .list(q="name='backups'", fields="nextPageToken, files(id, name)")
        .execute()
    )
    items = results.get("files", [])

    if not items:
        print("No files found.")
    else:
        print("Files:")
        for item in items:
            print(u"{0} ({1})".format(item["name"], item["id"]))


if __name__ == "__main__":
    main()
