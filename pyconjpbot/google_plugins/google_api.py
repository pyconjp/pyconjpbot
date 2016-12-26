import httplib2

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

SCOPES = [
    # Google Spreadseets
    # https://developers.google.com/sheets/api/guides/authorizing
    'https://spreadsheets.google.com/feeds',
    # Google Drive
    # https://developers.google.com/drive/v3/web/about-auth
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    # Google Calendar
    # https://developers.google.com/google-apps/calendar/auth
    'https://www.googleapis.com/auth/calendar.readonly',
    # Google Directory
    # https://developers.google.com/admin-sdk/directory/v1/guides/authorizing
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    ]
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'pyconjpbot'
CREDENTIAL_PATH = 'credentials.json'


def get_credentials():
    """
    credentialsファイルを生成する
    """
    credential_path = CREDENTIAL_PATH
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('credentialsを{}に保存しました'.format(credential_path))
    return credentials


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('直近の5件のイベントを表示')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=5, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])


if __name__ == '__main__':
    main()
