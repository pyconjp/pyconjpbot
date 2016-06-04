import argparse
import httplib2
import os
import json

from slackbot.bot import respond_to
from apiclient import discovery
from oauth2client import client
from oauth2client import file
from oauth2client import tools

# Google Drive API の Scope
SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'

# PyCon JP 関連の検索対象とする親フォルダの Id
FOLDER = {
    'PyCon JP': '0BzmtypRXAd8zZDZhOWJkNWQtMDNjOC00NjQ1LWI0YzYtZDU3NzY1NTY5NDM3',
    '一社': '0B_bw8GEmTD5OQmxBZ1l6UzNodmc',
    '2016': '0B_bw8GEmTD5OTTl1U0pWeW43Sk0',
    '全体': '0B_bw8GEmTD5OU1BWd0xBZWRkQkk',
    '事務局': '0B_bw8GEmTD5OTDd6Z2NJWTd0RW8',
    '会場': '0B_bw8GEmTD5OQjBpc00zRlo3RU0',
    'プログラム': '0B_bw8GEmTD5OemhocVR1a1ViOFU',
    'メディア': '0B_bw8GEmTD5OUmFFdVV1S0NKU2c',
    '議事録': '0B_bw8GEmTD5OZEJxZ2pBc0NmUWs',
    '2015': '0B_bw8GEmTD5ORXAtU28xNC0tTDg',
    '2014': '0B_bw8GEmTD5OZ0FCNXlWSTEtOU0',
    '2013': '0BzmtypRXAd8zR3FQWkhKY3luajg',
    '2012': '0B08rY0k8XSeVZjEzNzYyYjktNzc1Mi00N2Q0LTgxZjYtMzMyZjk2Yjg3ZDBl',
    '2011': '0BzmtypRXAd8zNGRiNmQyYTUtZTFjMS00ZGYwLWJhMGItZWU3ZTEyYjJlMWU1',
    'mini': '0BzmtypRXAd8zODdjODljOTctOWU5ZS00ZWJjLTk4MjgtNDMyZDExODA1NzQ0',
    }

MIME_TYPE = {
    'application/vnd.google-apps.spreadsheet': 'スプレッドシート',
    'application/vnd.google-apps.document': 'ドキュメント',
    'application/vnd.google-apps.presentation': 'スライド',
    'application/vnd.google-apps.folder': 'フォルダ',
    'application/vnd.google-apps.form': 'フォーム',
    }

    
def get_service(name, version, filename, scope):
    """指定された Google API に接続する

    name: APIの名前
    version: APIのバージョン(通常 v3)
    file: ファイルの場所を指定する、通常 __file__ を使用する
    scope: OAuth のスコープを指定する

    serviceオブジェクトを返す
    """

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

    # Name of a file containing the OAuth 2.0 information for this
    # application, including client_id and client_secret, which are found
    # on the API Access tab on the Google APIs
    # Console <http://code.google.com/apis/console>.
    client_secrets = os.path.join(os.path.dirname(filename),
                                  'client_secrets.json')

    # Set up a Flow object to be used if we need to authenticate.
    flow = client.flow_from_clientsecrets(
        client_secrets,
        scope=scope,
        message=tools.message_if_missing(client_secrets))

    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native
    # client flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    storagefile = os.path.join(os.path.dirname(filename),
                               name + '.dat')
    storage = file.Storage(storagefile)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http = httplib2.Http())

    service = discovery.build(name, version, http=http)
    return service

# APIに接続する
service = get_service('drive', 'v3', __file__, SCOPES)

@respond_to('drive (.*)')
def drive_search(message, keywords):
    query = 'fullText contains "{}"'.format(keywords)
    query += ' and "{}" in parents'.format(FOLDER['2016'])
    results = service.files().list(
        pageSize=10, fields="files(id, name, mimeType, webViewLink)", q=query).execute()

    items = results.get('files', [])
    if not items:
        message.send('ありませんでした')
        return

    pretext = '「{}」の検索結果'.format(keywords)
    text = ''
    for item in items:
        item['type'] = MIME_TYPE.get(item['mimeType'], item['mimeType'])
        text += '- <{webViewLink}|{name}> ({type}) \n'.format(**item)

    attachments = [{
        'fallback': pretext,
        'pretext': pretext,
        'text': text,
    }]
    message.send_webapi('', json.dumps(attachments))

def main():
    """
    Google Drive APIを認証して使用できるようにする
    """
    service = get_service('drive', 'v3', __file__, SCOPES)

    results = service.files().list(
        pageSize=10, fields="nextPageToken, files", q='fullText contains "名簿" and "{}" in parents or "{}" in parents'.format(FOLDER['2016'], FOLDER['2015'])).execute()
    for item in results.get('files', []):
        print(item['name'], item['id'])
        print(item['webViewLink'])

if __name__ == '__main__':
    main()
