from slackbot.bot import respond_to
from googleapiclient.errors import HttpError

from .google_api import get_service

DOMAIN = 'pycon.jp'

# https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/index.html

HELP = '''
- `gadmin user list`:
- `gadmin group list`:
- `gadmin member list (groupname)`:
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
    msg = '*{}* ユーザー\n'.format(count) + msg
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
    msg = '*{}* グループ\n'.format(count) + msg
    message.send(msg)


@respond_to('^gadmin\s+member\s+list\s(.*)')
def gadmin_member_list(message, key):
    """
    グループのメンバー一覧を返す

    :param key: グループのメールアドレス
    """
    service = _get_service()
    key += '@' + DOMAIN
    try:
        members_list = service.members().list(groupKey=key).execute()
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
