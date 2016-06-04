import json

from slackbot.bot import respond_to
#from pyconjpbot.plugins import google_api_tool
import google_api_tool

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

service = google_api_tool.get_service('drive', 'v3', __file__, SCOPES)

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
    service = google_api_tool.get_service('drive', 'v3', __file__, SCOPES)

    results = service.files().list(
        pageSize=10, fields="nextPageToken, files", q='fullText contains "名簿" and "{}" in parents or "{}" in parents'.format(FOLDER['2016'], FOLDER['2015'])).execute()
    for item in results.get('files', []):
        print(item['name'], item['id'])
        print(item['webViewLink'])

if __name__ == '__main__':
    main()
