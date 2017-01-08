from slackbot.bot import respond_to
from slackbot import settings
from slacker import Slacker
from googleapiclient.errors import HttpError

from .google_api import get_service

DOMAIN = 'pycon.jp'

# https://developers.google.com/admin-sdk/directory/v1/reference/?hl=ja
# https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/index.html

HELP = '''
- `$gadmin user list`: ユーザーの一覧を返す

- `$gadmin group list`: グループの一覧を返す

- `$gadmin member list (group)`: 指定したグループのメンバー一覧を返す
- `$gadmin member insert (group) (email)`: 指定したグループにメンバーを追加する
- `$gadmin member delete (group) (email)`: 指定したグループからメンバーを削除する
'''


def _get_service():
    """
    Google Apps Admin SDK の Directory API に接続する
    """
    service = get_service('admin', 'directory_v1')
    return service


@respond_to('^gadmin\s+user\s+list')
def gadmin_user_list(message):
    """
    ユーザーの一覧を返す
    """

    service = _get_service()
    users_list = service.users().list(orderBy='email', domain=DOMAIN).execute()

    count = 0
    msg = ''
    for user in users_list.get('users', []):
        email = user['primaryEmail']
        fullname = user['name']['fullName']
        msg += '- {} {}\n'.format(email, fullname)
        count += 1
    msg = '{}ドメインのユーザー一覧({}ユーザー)\n'.format(DOMAIN, count) + msg
    message.send(msg)


@respond_to('^gadmin\s+group\s+list')
def gadmin_group_list(message):
    """
    グループの一覧を返す
    """
    service = _get_service()
    groups_list = service.groups().list(domain=DOMAIN).execute()

    count = 0
    msg = ''
    for group in groups_list.get('groups', []):
        email = group['email']
        name = group['name']
        member_count = group['directMembersCount']
        msg += '- {} {}({}ユーザー)\n'.format(email, name, member_count)
        count += 1
    msg = '{}ドメインのグループ一覧({}グループ)\n'.format(DOMAIN, count) + msg
    message.send(msg)


@respond_to('^gadmin\s+member\s+list\s+(.*)')
def gadmin_member_list(message, key):
    """
    グループのメンバー一覧を返す

    :param key: グループのメールアドレス(@の前の部分)
    """
    service = _get_service()
    group = '{}@{}'.format(key, DOMAIN)
    try:
        members_list = service.members().list(groupKey=group).execute()
    except HttpError:
        message.send('`{}` に合致するグループはありません'.format(key))
        return

    count = 0
    msg = ''
    for member in members_list.get('members', []):
        email = member['email']
        msg += '- {}\n'.format(email)
        count += 1
    msg = '*{}* グループのメンバー({}ユーザー)\n'.format(key, count) + msg
    message.send(msg)


def _is_admin(user):
    """
    ユーザーがSlackのAdminかどうかを返す

    :param user: SlackのユーザーID
    """
    slack = Slacker(settings.API_TOKEN)
    user_info = slack.users.info(user)
    return user_info.body['user']['is_admin']


def _remove_email_link(email):
    """
    slack の email 記法 <mailto:hoge@example.com|hoge@example.com> を
    メールアドレスのみに戻す
    """

    email = email.replace('<mailto:', '')
    if '|' in email:
        email, _ = email.split('|', 2)
    return email


@respond_to('^gadmin\s+member\s+insert\s+(.*)\s+(.*)')
def gadmin_member_insert(message, key, email):
    """
    指定したメンバーを指定したグループに追加する

    :param key: グループのメールアドレス(@の前の部分)
    :param mail: 追加するメンバーのメールアドレス
    """
    # コマンドを実行したユーザーのIDを取得
    user = message.body['user']
    if not _is_admin(user):
        message.sent('このコマンドの実行にはAdmin以上の権限が必要です')

    # 追加するメンバーの情報を作成する
    email = _remove_email_link(email)
    group = '{}@{}'.format(key, DOMAIN)
    service = _get_service()
    body = {
        'email': email,
    }
    try:
        service.members().insert(groupKey=group, body=body).execute()
    except HttpError as e:
        message.send('メンバーの追加に失敗しました\n`{}`'.format(e))
        return
    message.send('`{}` グループに `{}` を追加しました'.format(group, email))


@respond_to('^gadmin\s+member\s+delete\s+(.*)\s+(.*)')
def gadmin_member_delete(message, key, email):
    """
    指定したメンバーを指定したグループから削除する

    :param key: グループのメールアドレス(@の前の部分)
    :param mail: 削除するメンバーのメールアドレス
    """
    # コマンドを実行したユーザーのIDを取得
    user = message.body['user']
    if not _is_admin(user):
        message.sent('このコマンドの実行にはAdmin以上の権限が必要です')

    # 追加するメンバーの情報を作成する
    email = _remove_email_link(email)
    group = '{}@{}'.format(key, DOMAIN)
    service = _get_service()
    try:
        service.members().delete(groupKey=group, memberKey=email).execute()
    except HttpError as e:
        message.send('メンバーの削除に失敗しました\n`{}`'.format(e))
        return
    message.send('`{}` グループから `{}` を削除しました'.format(group, email))


@respond_to('^gadmin\s+help')
def gadmin_help(message):
    """
    コマンドのヘルプを表示
    """
    message.send(HELP)
