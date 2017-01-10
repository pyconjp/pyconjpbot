import string
import random

from slackbot.bot import respond_to
from slackbot import settings
from slacker import Slacker
from googleapiclient.errors import HttpError

from .google_api import get_service

DOMAIN = 'pycon.jp'

# https://developers.google.com/admin-sdk/directory/v1/reference/?hl=ja
# https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/index.html

HELP = '''

ユーザー管理

- `$gadmin user list`: ユーザーの一覧を返す
- `$gadmin user insert user firstname lastname`: ユーザーを追加する
- `$gadmin user delete user`: ユーザーを削除する(停止中のみ削除可)
- `$gadmin user reset user`: ユーザーのパスワードをリセットする
- `$gadmin user suspend user`: ユーザーを停止する(停止中にする)
- `$gadmin user resume user`: ユーザーを再開する(アクティブにする)

メールのエイリアス管理

- `$gadmin alias list user`: ユーザーのエイリアスの一覧を返す
- `$gadmin alias insert user alias`: ユーザーにエイリアスを追加する
- `$gadmin alias delete user alias`: ユーザーからエイリアスを削除する

グループ管理

- `$gadmin group list`: グループの一覧を返す
- `$gadmin group insert group group-name`: 指定したグループを追加する
- `$gadmin group delete group`: 指定したグループを削除する

グループのメンバー管理

- `$gadmin member list group`: 指定したグループのメンバー一覧を返す
- `$gadmin member insert group email1 [email2...]`: 指定したグループにメンバーを追加する
- `$gadmin member delete group email1 [email2...]`: 指定したグループからメンバーを削除する
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


def _get_default_domain_email(email):
    """
    ドメインがない場合は、デフォルトのドメインを追加したメールアドレスを返す
    """
    email = _remove_email_link(email)
    if '@' not in email:
        email += '@' + DOMAIN
    return email


def _generate_password(length=8):
    """
    パスワード用の文字列を生成する

    :param length: パスワードの長さ
    """
    text = string.ascii_letters + string.digits
    password = ''.join(random.sample(text, length))
    return password


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


def _gadmin_user_insert(service, message, email, fname, lname):
    """
    指定したユーザーを追加する

    :param service: Google API との接続
    :param email: メールアドレス
    :param fname: ユーザーのfirst name(insert時に使用)
    :param fname: ユーザーのlast name(insert時に使用)
    """
    # パスワードを生成する
    password = _generate_password()
    body = {
        'primaryEmail': email,
        'password': password,
        'name': {
            'givenName': fname.title(),
            'familyName': lname.title(),
        },
    }
    try:
        service.users().insert(body=body).execute()
        message.send('ユーザー `{}` を追加しました'.format(email))
        # TODO: password をユーザーにDMで伝える
    except HttpError as e:
        message.send('ユーザーの追加に失敗しました\n`{}`'.format(e))


def _gadmin_user_delete(service, message, email):
    """
    指定したユーザーを削除する

    :param service: Google API との接続
    :param email: メールアドレス
    """
    try:
        # 停止中のユーザーのみ削除対象とする
        result = service.users().get(userKey=email).execute()
        if not result['suspended']:
            message.send('ユーザーはアクティブなため削除できません\n'
                         '`$gadmin user suspend {}` でユーザーを停止してから削除してください'.format(email))
        else:
            service.users().delete(userKey=email).execute()
            message.send('ユーザー `{}` を削除しました'.format(email))
    except HttpError as e:
        message.send('ユーザーの削除に失敗しました\n`{}`'.format(e))


def _gadmin_user_update(service, message, email, suspended):
    """
    ユーザーの情報を更新する

    :param service: Google API との接続
    :param email: メールアドレス
    :param suspended: ユーザーの状態、True or False
    """
    body = {
        'suspended': suspended,
    }
    try:
        service.users().update(userKey=email, body=body).execute()
        if suspended:
            message.send('ユーザー `{}` を停止しました'.format(email))
        else:
            message.send('ユーザー `{}` を再開しました'.format(email))
    except HttpError as e:
        message.send('ユーザー情報の更新に失敗しました\n`{}`'.format(e))


@respond_to('^gadmin\s+user\s+(insert)\s+(\S+)\s+(\S+)\s+(\S+)')
@respond_to('^gadmin\s+user\s+(delete|suspend|resume|reset)\s+(\S+)')
def gadmin_user_insert_delete(message, command, email, fname=None, lname=None):
    """
    指定したユーザーを追加/削除する

    - `$gadmin user insert user firstname lastname`: ユーザーを追加する
    - `$gadmin user delete user`: ユーザーを削除する(停止中のみ削除可)
    - `$gadmin user reset user`: ユーザーのパスワードをリセットする
    - `$gadmin user suspend user`: ユーザーを停止する(停止中にする)
    - `$gadmin user resume user`: ユーザーを再開する(アクティブにする)

    :param command: コマンド(insert または delete)
    :param email: メールアドレス
    :param fname: ユーザーのfirst name(insert時に使用)
    :param fname: ユーザーのlast name(insert時に使用)
    """
    # コマンドを実行したユーザーのIDを取得
    user = message.body['user']
    if not _is_admin(user):
        message.sent('このコマンドの実行にはAdmin以上の権限が必要です')

    service = _get_service()
    email = _get_default_domain_email(email)

    if command == 'insert':
        _gadmin_user_insert(service, message, email, fname, lname)
    elif command == 'delete':
        _gadmin_user_delete(service, message, email)
    elif command == 'suspend':
        # ユーザーを停止して停止中にする
        _gadmin_user_update(service, message, email, suspended=True)
    elif command == 'resume':
        # ユーザーを再開してアクティブにする
        _gadmin_user_update(service, message, email, suspended=False)


@respond_to('^gadmin\s+alias\s+list\s+(.*)')
def gadmin_alias_list(message, email):
    """
    指定したユーザーのエイリアスの一覧を返す

    :param email: メールアドレス
    """

    service = _get_service()
    email = _get_default_domain_email(email)
    try:
        result = service.users().aliases().list(userKey=email).execute()
        msg = ''
        aliases = result.get('aliases', [])
        if aliases:
            msg = '`{}` のエイリアス一覧\n'.format(email)
            msg += ', '.join('`{}`'.format(alias['alias']) for alias in aliases)
            message.send(msg)
        else:
            msg = '`{}` のエイリアスはありません'.format(email)
            message.send(msg)
    except HttpError as e:
        message.send('エイリアスの取得失敗しました\n`{}`'.format(e))


def _gadmin_alias_insert(service, message, email, alias):
    """
    指定したユーザーにエイリアスを追加する

    :param service: Google API との接続
    :param email: 追加対象のメールアドレス
    :param alias: エイリアスのメールアドレス
    """
    body = {
        'alias': alias,
    }
    try:
        service.users().aliases().insert(userKey=email, body=body).execute()
        message.send('`{}` にエイリアス `{}` を追加しました'.format(email, alias))
    except HttpError as e:
        message.send('エイリアスの追加に失敗しました\n`{}`'.format(e))


def _gadmin_alias_delete(service, message, email, alias):
    """
    指定したユーザーからエイリアスを削除する

    :param service: Google API との接続
    :param email: 追加対象のメールアドレス
    :param alias: エイリアスのメールアドレス
    """
    try:
        service.users().aliases().delete(userKey=email, alias=alias).execute()
        message.send('`{}` からエイリアス `{}` を削除しました'.format(email, alias))
    except HttpError as e:
        message.send('エイリアスの削除に失敗しました\n`{}`'.format(e))


@respond_to('^gadmin\s+alias\s+(insert|delete)\s+(.*)\s+(.*)')
def gadmin_alias_insert_delete(message, command, email, alias):
    """
    指定したユーザーにエイリアスを追加/削除する

    - `$gadmin alias insert (email) (alias)`
    - `$gadmin alias delete (email) (alias)`

    :param command: コマンド(insert または delete)
    :param email: メールアドレス
    :param alias: エイリアスのメールアドレス
    """
    service = _get_service()
    email = _get_default_domain_email(email)
    alias = _get_default_domain_email(alias)

    if command == 'insert':
        _gadmin_alias_insert(service, message, email, alias)
    elif command == 'delete':
        _gadmin_alias_delete(service, message, email, alias)


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
    group = _get_default_domain_email(group)
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
    group = _get_default_domain_email(group)
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
    group = _get_default_domain_email(group)
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
