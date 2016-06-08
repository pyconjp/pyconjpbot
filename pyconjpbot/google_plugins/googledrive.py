import argparse
import httplib2
import os
import os.path
import json

from slackbot.bot import respond_to
from apiclient import discovery
from oauth2client import client
from oauth2client import file
from oauth2client import tools

from .folder_model import Folder

# Google Drive API の Scope
SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'

# PyCon JP のルートフォルダのID
ROOT_FOLDER_NAME = 'PyCon JP/'
ROOT_FOLDER_ID = '0BzmtypRXAd8zZDZhOWJkNWQtMDNjOC00NjQ1LWI0YzYtZDU3NzY1NTY5NDM3'

# MIME_TYPE とそれに対応する名前の辞書
MIME_TYPE = {
    'application/vnd.google-apps.spreadsheet': 'スプレッドシート',
    'application/vnd.google-apps.document': 'ドキュメント',
    'application/vnd.google-apps.presentation': 'スライド',
    'application/vnd.google-apps.folder': 'フォルダ',
    'application/vnd.google-apps.form': 'フォーム',
    }

# MIME_TYPE の key と value を逆にした辞書
MIME_TYPE_INV = {value: key for key, value in MIME_TYPE.items()}

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
    if keywords in ('update', 'help'):
        return
    
    query = 'fullText contains "{}"'.format(keywords)
    #query += ' and "{}" in parents'.format(FOLDER['2016'])
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

@respond_to('drive update')
def drive_update(message):
    """
    フォルダーのパスとidを入れたデータベースを更新する
    """
    service = get_service('drive', 'v3', __file__, SCOPES)
    message.send('データベースを更新します')

    # テーブルを生成する
    Folder.drop_table()
    Folder.create_table(fail_silently=True)
    # Google Drive のフォルダ階層を走査する
    _drive_walk(service, ROOT_FOLDER_NAME + '/', ROOT_FOLDER_ID)
    
    message.send('データベースを更新を完了しました')

def _drive_walk(service, path, folder_id):
    """
    フォルダの階層をたどる
    """
    #print("フォルダ: {}".format(path))
    # フォルダのみを取得する 
    q = "'{}' in parents and mimeType = '{}'".format(
        folder_id, MIME_TYPE_INV['フォルダ'])
    response = service.files().list(fields="files(id, name)", q=q).execute()

    for file in response.get('files', []):
        new_path = path + file.get('name') + '/'

        # データベースに追加(INSERT)または更新(REPLACE)する
        fields = {'path': new_path, 'id': file.get('id')}
        Folder.insert(fields).upsert(upsert=True).execute()

        # 下の階層を処理する
        _drive_walk(service, new_path, file.get('id'))
