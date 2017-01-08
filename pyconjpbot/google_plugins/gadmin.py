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
- `$gadmin group insert (group) (name)`: 指定したグループを追加する
- `$gadmin group delete (group)`: 指定したグループを削除する

- `$gadmin member list (group)`: 指定したグループのメンバー一覧を返す
- `$gadmin member insert (group) (email...)`: 指定したグループにメンバーを追加する
- `$gadmin member delete (group) (email...)`: 指定したグループからメンバーを削除する
'''


def _get_service():
    """
    Google Apps Admin SDK の Directory API に接続する
    """
    service = get_service('admin', 'directory_v1')
    return service


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


def _gadmin_group_insert(message, service, group, name):
    """
    指定したグループを追加する

    :param service: Google API との接続
    :param group: グループのメールアドレス
    :param name: グループの名前
    """
    body = {
        'name': name,
        'email': group,
    }
    try:
        service.groups().insert(body=body).execute()
    except HttpError as e:
        message.send('グループの追加に失敗しました\n`{}`'.format(e))
        return
    message.send('`{}` グループを追加しました'.format(group))
    message.send('`$gadmin member insert {} メールアドレス` コマンドでメンバーを追加してください'.format(group))


def _gadmin_group_delete(message, service, group):
    """
    指定したグループを削除する

    :param service: Google API との接続
    :param group: グループのメールアドレス
    """
    try:
        result = service.groups().get(groupKey=group).execute()
        count = result['directMembersCount']
        if count != '0':
            # メンバーがいる場合は削除できない
            message.send('''
`{group}` グループはメンバーがいるので削除できません
`$gadmin member delete {group} メールアドレス` コマンドでメンバーを削除してから実行してください
`$gadmin member list {group}` コマンドでメンバー一覧が確認できます
'''.format(group=group))
        else:
            service.groups().delete(groupKey=group).execute()
            message.send('`{}` グループを削除しました'.format(group))
    except HttpError as e:
        message.send('グループの削除に失敗しました\n`{}`'.format(e))
        return


@respond_to('^gadmin\s+group\s+(insert)\s+(.*)\s+(.*)')
@respond_to('^gadmin\s+group\s+(delete)\s+(.*)')
def gadmin_group_insert_delete(message, command, group, name=None):
    """
    指定したグループを追加/削除する

    - `$gadmin group insert (group) (name)`
    - `$gadmin group delete (group)`

    :param group: グループのメールアドレスまたは@の前の部分
    :param name: グループの名前
    """
    # コマンドを実行したユーザーのIDを取得
    user = message.body['user']
    if not _is_admin(user):
        message.sent('このコマンドの実行にはAdmin以上の権限が必要です')

    # グループ、メンバー情報の前処理
    group = _remove_email_link(group)
    if '@' not in group:
        group += '@' + DOMAIN
    service = _get_service()
    if command == 'insert':
        _gadmin_group_insert(message, service, group, name)
    elif command == 'delete':
        _gadmin_group_delete(message, service, group)


@respond_to('^gadmin\s+member\s+list\s+(.*)')
def gadmin_member_list(message, group):
    """
    グループのメンバー一覧を返す

    :param key: グループのメールアドレス(@の前の部分)
    """
    service = _get_service()
    group = _remove_email_link(group)
    if '@' not in group:
        group += '@' + DOMAIN
    try:
        members_list = service.members().list(groupKey=group).execute()
    except HttpError:
        message.send('`{}` に合致するグループはありません'.format(group))
        return

    count = 0
    msg = ''
    for member in members_list.get('members', []):
        email = member['email']
        msg += '- {}\n'.format(email)
        count += 1
    msg = '*{}* グループのメンバー({}ユーザー)\n'.format(group, count) + msg
    message.send(msg)


def _gadmin_member_insert(message, service, group, emails):
    """
    指定したメンバーを指定したグループに追加する

    :param service: Google API との接続
    :param group: グループのメールアドレス
    :param mail: 追加/削除するメンバーのメールアドレス
    """

    for email in emails:
        body = {
            'email': email,
        }
        try:
            service.members().insert(groupKey=group, body=body).execute()
            message.send('`{}` グループに `{}` を追加しました'.format(group, email))
        except HttpError as e:
            # TODO: グループが間違っている場合とメンバーのエラーの場合わけ
            message.send('メンバーの追加に失敗しました\n`{}`'.format(e))


def _gadmin_member_delete(message, service, group, emails):
    """
    指定したメンバーを指定したグループから削除する

    :param service: Google API との接続
    :param group: グループのメールアドレス
    :param mail: 追加/削除するメンバーのメールアドレス
    """
    for email in emails:

        try:
            service.members().delete(groupKey=group, memberKey=email).execute()
            message.send('`{}` グループから `{}` を削除しました'.format(group, email))
        except HttpError as e:
            # TODO: グループが間違っている場合とメンバーのエラーの場合わけ
            message.send('メンバーの削除に失敗しました\n`{}`'.format(e))


@respond_to('^gadmin\s+member\s+(insert|delete)\s+(\S*)\s+(.*)')
def gadmin_member_insert_delete(message, command, group, email):
    """
    指定したメンバーを指定したグループに追加/削除する

    - `$gadmin member insert (group) (email...)`
    - `$gadmin member delete (group) (email...)`

    :param group: グループのメールアドレスまたは@の前の部分
    :param mail: 追加/削除するメンバーのメールアドレス
    """
    # コマンドを実行したユーザーのIDを取得
    user = message.body['user']
    if not _is_admin(user):
        message.sent('このコマンドの実行にはAdmin以上の権限が必要です')

    # グループ、メンバー情報の前処理
    emails = []
    for email in email.split():
        email = _remove_email_link(email)
        if '@' in email:
            emails.append(email)
    group = _remove_email_link(group)
    if '@' not in group:
        group += '@' + DOMAIN
    service = _get_service()

    # 対象となるメールアドレスがある場合のみ処理する
    if emails:
        if command == 'insert':
            _gadmin_member_insert(message, service, group, emails)
        elif command == 'delete':
            _gadmin_member_delete(message, service, group, emails)
    else:
        message.send('正しいメールアドレスを指定してください')


@respond_to('^gadmin\s+help')
def gadmin_help(message):
    """
    コマンドのヘルプを表示
    """
    message.send(HELP)
