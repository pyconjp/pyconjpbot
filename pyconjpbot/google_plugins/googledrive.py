import argparse
import json
from collections import OrderedDict

from slackbot.bot import respond_to

from .folder_model import Folder
from .google_api import get_service

# Google Drive API の Scope
SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'

# PyCon JP のルートフォルダのID
ROOT_FOLDER_NAME = 'PyCon JP'
ROOT_FOLDER_ID = '0BzmtypRXAd8zZDZhOWJkNWQtMDNjOC00NjQ1LWI0YzYtZDU3NzY1NTY5NDM3'

# 検索対象のフォルダのパス
FOLDER = OrderedDict([
    ('2017', 'PyCon JP/2017/'),
    ('2016', 'PyCon JP/2016/'),
    ('事務局', 'PyCon JP/2016/1.事務局/'),
    ('会場', 'PyCon JP/2016/2.会場/'),
    ('プログラム', 'PyCon JP/2016/3.プログラム/'),
    ('メディア', 'PyCon JP/2016/4.メディア/'),
    ('2015', 'PyCon JP/2015/'),
    ('2014', 'PyCon JP/2014/'),
    ('2013', 'PyCon JP/2013/'),
    ('2012', 'PyCon JP/2012/'),
    ('一社', 'PyCon JP/一般社団法人/'),
])

# ファイルの種類と MIME_TYPE の辞書
MIME_TYPE = OrderedDict([
    ('フォルダ', 'application/vnd.google-apps.folder'),
    ('スプレッドシート', 'application/vnd.google-apps.spreadsheet'),
    ('ドキュメント', 'application/vnd.google-apps.document'),
    ('スライド', 'application/vnd.google-apps.presentation'),
    ('フォーム', 'application/vnd.google-apps.form'),
])

# MIME_TYPE の key と value を逆にした辞書
MIME_TYPE_INV = {value: key for key, value in MIME_TYPE.items()}

# $dive コマンドの引数処理用 arpparse
HELP = """
- `$drive [options] keywords`: 指定されたキーワードで検索する
- `$drive db update`: 検索用のフォルダ情報を更新する
- `$drive db refresh`: 検索用のフォルダ情報を再構築する
```
$drive [-n] [-l LIMIT] [-f FOLDER] [-t TYPE] keywords...`

オプション引数:

  -n, --name            ファイル名のみを検索対象にする(未指定時は全文検索)
  -l LIMIT, --limit LIMIT
                        結果の最大件数を指定する(default: 10)
  -f FOLDER, --folder FOLDER
                        検索対象のフォルダーを指定する(default: 2016)
  -t TYPE, --type TYPE  検索対象のファイル種別を指定する
```
"""
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-n', '--name', default=False, action='store_true',
                    help='ファイル名のみを検索対象にする(未指定時は全文検索)')
parser.add_argument('-l', '--limit', default=10, type=int,
                    help='結果の最大件数を指定する(default: 10)')
parser.add_argument('-f', '--folder', default='2016', type=str,
                    help='検索対象のフォルダーを指定する(default: 2016)')
parser.add_argument('-t', '--type', type=str,
                    help='検索対象のファイル種別を指定する')
parser.add_argument('keywords', nargs='+',
                    help='検索対象のキーワードを指定する')


def _build_query(args):
    """
    Google Drive を検索するための query を生成する

    args.keywords: キーワードのリスト
    args.name: True の場合、ファイル名で検索
    args.folder: 指定されたフォルダーを検索対象とする
    args.type: ファイルの種類(mimeType)

    参考: https://developers.google.com/drive/v3/web/search-parameters
    """
    
    # デフォルトは全文検索
    target = 'fullText'
    if args.name:
        # ファイル名のみを対象にする
        target = 'name'

    # キーワードは and 検索
    # 例: name contains key1 and name contains key2...
    keyword_queries = ["{} contains '{}'".format(target, x) for x in args.keywords]
    query = ' and '.join(keyword_queries)

    # mime_type が指定されている場合
    # 例: mimeType = 'application/vnd.google-apps.folder'
    if args.type:
        query += " and mimeType = '{}'".format(MIME_TYPE[args.type])

    # 対象となるパスのフォルダ一覧を取得
    path = FOLDER[args.folder] + "*"
    folders = Folder.select().where(Folder.path % path)

    # フォルダーは or 検索
    # 例: '12345' in parents or '12346' in parents...
    folder_queries = ["'{}' in parents".format(x.id) for x in folders]
    query += ' and (' + ' or '.join(folder_queries) + ')'

    return query


@respond_to('drive (.*)')
def drive_search(message, keywords):
    """
    指定されたキーワードに対して検索を行う

    -n, --name            ファイル名のみを検索対象にする(未指定時は全文検索)
    -l LIMIT, --limit LIMIT
                          結果の最大件数を指定する(default: 10)
    -f FOLDER, --folder FOLDER
                          検索対象のフォルダーを指定する(default: 2016)
    -t TYPE, --type TYPE  検索対象のファイル種別を指定する
    """

    if keywords in ('db update', 'db refresh', 'help'):
        return

    # 引数を処理する
    try:
        args, argv = parser.parse_known_args(keywords.split())
    except SystemExit:
        message.send('引数の形式が正しくありません')
        _drive_help(message)
        return

    if args.folder and args.folder not in FOLDER:
        folders = ', '.join(["`" + x + "`" for x in FOLDER])
        message.send('フォルダーの指定が正しくありません。以下のフォルダーが指定可能です。\n' + folders)
        _drive_help(message)
        return
        
    if args.type and args.type not in MIME_TYPE:
        mime_types = ', '.join(["`" + x + "`" for x in MIME_TYPE])
        message.send('ファイル種別の指定が正しくありません。以下のファイルが指定可能です。\n' + mime_types)
        _drive_help(message)
        return

    # 引数から query を生成
    q = _build_query(args)

    # Google Drive API で検索を実行する
    service = get_service('drive', 'v3')
    fields = "files(id, name, mimeType, webViewLink, modifiedTime)"
    results = service.files().list(pageSize=args.limit, fields=fields, q=q).execute()

    items = results.get('files', [])
    if not items:
        message.send('パラメーター: `{}` にマッチするファイルはありません'.format(keywords))
        return

    pretext = 'パラメーター: `{}` の検索結果'.format(keywords)
    text = ''
    for item in items:
        item['type'] = MIME_TYPE_INV.get(item['mimeType'], item['mimeType'])
        text += '- <{webViewLink}|{name}> ({type}) \n'.format(**item)

    attachments = [{
        'fallback': pretext,
        'pretext': pretext,
        'text': text,
        'mrkdwn_in': ["pretext"],
    }]
    message.send_webapi('', json.dumps(attachments))


def _drive_db_update():
    """
    フォルダーのパスとidを入れたデータベースを更新する
    """
    service = get_service('drive', 'v3')
    Folder.create_table(fail_silently=True)
    # Google Drive のフォルダ階層を走査する
    _drive_walk(service, ROOT_FOLDER_NAME + '/', ROOT_FOLDER_ID)


@respond_to('drive db update')
def drive_db_update(message):
    """
    フォルダーのパスとidを入れたデータベースを更新する
    """
    message.send('データベースを更新します')
    _drive_db_update()
    message.send('データベースを更新を完了しました')


@respond_to('drive db refresh')
def drive_db_refresh(message):
    """
    フォルダーのパスとidを入れたデータベースを最初から作成し直す
    """
    message.send('データベースを再構築します')

    # テーブルを削除する
    Folder.drop_table()
    _drive_db_update()

    message.send('データベースを再構築を完了しました')


def _drive_walk(service, path, folder_id):
    """
    フォルダの階層をたどる
    """
    # print("フォルダ: {}".format(path))
    # フォルダのみを取得する
    q = "'{}' in parents and mimeType = '{}'".format(
        folder_id, MIME_TYPE['フォルダ'])
    response = service.files().list(fields="files(id, name)", q=q).execute()

    for file in response.get('files', []):
        new_path = path + file.get('name') + '/'

        # データベースに追加(INSERT)または更新(REPLACE)する
        fields = {'path': new_path, 'id': file.get('id')}
        Folder.insert(fields).upsert(upsert=True).execute()

        # 下の階層を処理する
        _drive_walk(service, new_path, file.get('id'))


@respond_to('drive help$')
def drive_help(message):
    _drive_help(message)


def _drive_help(message):
    message.send(HELP)
