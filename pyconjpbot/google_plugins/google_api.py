import os.path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

SCOPES = [
    # Google Spreadseets
    # https://developers.google.com/sheets/api/guides/authorizing
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    # Google Drive
    # https://developers.google.com/drive/v3/web/about-auth
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    # Google Calendar
    # https://developers.google.com/google-apps/calendar/auth
    "https://www.googleapis.com/auth/calendar.readonly",
    # Google Directory
    # https://developers.google.com/admin-sdk/directory/v1/guides/authorizing
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/admin.directory.user",
]

APPLICATION_NAME = "pyconjpbot"
CREDENTIAL_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def get_service(name: str, version: str) -> Resource:
    """指定された Google API に接続する

    name: APIの名前
    version: APIのバージョン
    scope: OAuth のスコープを指定する

    serviceオブジェクトを返す
    """
    credentials = get_credentials()
    service = build(name, version, credentials=credentials)
    return service


def get_credentials():
    """
    credentials情報を作成して返す
    """

    creds = None

    dirname = os.path.dirname(__file__)
    credential_file = os.path.join(dirname, CREDENTIAL_FILE)
    token_file = os.path.join(dirname, TOKEN_FILE)

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credential_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    return creds


def main() -> None:
    # calendar APIの動作確認
    service = get_service("calendar", "v3")

    now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    print("直近の5件のイベントを表示")
    eventsResult = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=5,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = eventsResult.get("items", [])

    if not events:
        print("No upcoming events found.")
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        print(start, event["summary"])

    # Directory APIの動作確認
    # https://developers.google.com/admin-sdk/directory/v1/quickstart/python
    print("10名のユーザーを表示")
    service = get_service("admin", "directory_v1")

    results = (
        service.users()
        .list(domain="pycon.jp", maxResults=10, orderBy="email")
        .execute()
    )
    users = results.get("users", [])
    for user in users:
        print(user["name"]["fullName"], user["primaryEmail"])


if __name__ == "__main__":
    main()
