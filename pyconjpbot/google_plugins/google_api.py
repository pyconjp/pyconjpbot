import os.path
from datetime import datetime

import httplib2
from apiclient import discovery
from oauth2client import client, tools
from oauth2client.file import Storage

SCOPES = [
    # Google Spreadseets
    # https://developers.google.com/sheets/api/guides/authorizing
    "https://spreadsheets.google.com/feeds",
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
CLIENT_SECRET_FILE = "client_secret.json"
APPLICATION_NAME = "pyconjpbot"
CREDENTIAL_FILE = "credentials.json"


def get_service(name, version):
    """指定された Google API に接続する

    name: APIの名前
    version: APIのバージョン
    scope: OAuth のスコープを指定する

    serviceオブジェクトを返す
    """
    credentials = get_credentials()
    http = credentials.authorize(http=httplib2.Http())
    service = discovery.build(name, version, http=http)
    return service


def get_credentials():
    """
    credentialsファイルを生成する
    """
    dirname = os.path.dirname(__file__)
    credential_path = os.path.join(dirname, CREDENTIAL_FILE)
    client_secret_file = os.path.join(dirname, CLIENT_SECRET_FILE)

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret_file, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print(f"credentialsを{credential_path}に保存しました")
    return credentials


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("calendar", "v3", http=http)

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


if __name__ == "__main__":
    main()
