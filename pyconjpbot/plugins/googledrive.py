import json

from slackbot.bot import respond_to
from pyconjpbot.plugins import google_api_tool

SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'

FOLDER = {
    '2016': '0B_bw8GEmTD5OTTl1U0pWeW43Sk0',
    '2015': '0B_bw8GEmTD5ORXAtU28xNC0tTDg',
    '2014': '0B_bw8GEmTD5OZ0FCNXlWSTEtOU0',
    '一般社団法人': '0B_bw8GEmTD5OQmxBZ1l6UzNodmc',
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
        pageSize=10, fields="nextPageToken, files", q='fullText contains "名簿" and "{}" in parents'.format(FOLDER['2016'])).execute()
    for item in results.get('files', []):
        print(item['name'], item['id'])
        print(item['webViewLink'])

if __name__ == '__main__':
    main()
