from __future__ import annotations

import random
import string

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from slack_sdk import WebClient
from slackbot import settings
from slackbot.bot import respond_to
from slackbot.dispatcher import Message

from ..botmessage import botsend
from .google_api import get_service

DOMAIN = "pycon.jp"

# https://developers.google.com/admin-sdk/directory
# https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/index.html

HELP = """

ユーザー管理

- `$gadmin user list`: ユーザーの一覧を返す
- `$gadmin user insert (ユーザー) (名前) (名字)`: ユーザーを追加する
- `$gadmin user delete  (ユーザー)`: ユーザーを削除する(停止中のみ削除可)
- `$gadmin user reset  (ユーザー)`: ユーザーのパスワードをリセットする
- `$gadmin user suspend  (ユーザー)`: ユーザーを停止する(停止中にする)
- `$gadmin user resume  (ユーザー)`: ユーザーを再開する(アクティブにする)

メールのエイリアス管理

- `$gadmin alias list (ユーザ)`: ユーザーのエイリアスの一覧を返す
- `$gadmin alias insert (ユーザ) (エイリアス)`: ユーザーにエイリアスを追加する
- `$gadmin alias delete (ユーザ) (エイリアス)`: ユーザーからエイリアスを削除する

グループ管理

- `$gadmin group list`: グループの一覧を返す
- `$gadmin group insert (グループ) (グループ名)`: 指定したグループを追加する
- `$gadmin group delete (グループ)`: 指定したグループを削除する

グループのメンバー管理

- `$gadmin member list (グループ)`: 指定したグループのメンバー一覧を返す
- `$gadmin member insert (グループ) (メール1) [(メール2...)]`: 指定したグループにメンバーを追加する
- `$gadmin member delete (グループ) (メール1) [(メール2...)]`: 指定したグループからメンバーを削除する
"""


def _get_service() -> Resource:
    """
    Google Apps Admin SDK の Directory API に接続する
    """
    service = get_service("admin", "directory_v1")
    return service


def _is_admin(user: str) -> bool:
    """
    ユーザーがSlackのAdminかどうかを返す

    :param user: SlackのユーザーID
    """
    client = WebClient(token=settings.API_TOKEN)
    user_info = client.users_info(user=user)
    return user_info["user"]["is_admin"]


def _remove_email_link(email: str) -> str:
    """
    slack の email 記法 <mailto:hoge@example.com|hoge@example.com> を
    メールアドレスのみに戻す
    """

    email = email.replace("<mailto:", "")
    if "|" in email:
        email, _ = email.split("|", 2)
    return email


def _get_default_domain_email(email: str) -> str:
    """
    ドメインがない場合は、デフォルトのドメインを追加したメールアドレスを返す
    """
    email = _remove_email_link(email)
    if "@" not in email:
        email += "@" + DOMAIN
    return email


def _generate_password(length: int = 8) -> str:
    """
    パスワード用の文字列を生成する

    :param length: パスワードの長さ
    """
    text = string.ascii_letters + string.digits
    password = "".join(random.sample(text, length))
    return password


def _send_password_on_dm(message: Message, email: str, password: str) -> None:
    """
    ユーザーのパスワード文字列を DM でコマンドを実行したユーザーに送信する

    :param email: ユーザーのメールアドレス
    :param password: 生成されたパスワード文字列
    """
    # ユーザーとのDMのチャンネルIDを取得
    user = message._body["user"]
    client = WebClient(token=settings.API_TOKEN)
    result = client.conversations_open(users=user)
    dm_channel = result["channel"]["id"]

    msg = f"ユーザー `{email}` のパスワードは `{password}` です"
    # DMチャンネルにメッセージを送信する
    client.chat_postMessage(channel=dm_channel, text=msg)


@respond_to(r"^gadmin\s+user\s+list")
def gadmin_user_list(message: Message) -> None:
    """
    ユーザーの一覧を返す
    """

    service = _get_service()
    users_list = service.users().list(orderBy="email", domain=DOMAIN).execute()

    count = 0
    msg = ""
    for user in users_list.get("users", []):
        email = user["primaryEmail"]
        fullname = user["name"]["fullName"]
        msg += f"- {email} {fullname}\n"
        count += 1
    msg = f"{DOMAIN}ドメインのユーザー一覧({count}ユーザー)\n{msg}"
    botsend(message, msg)


def _gadmin_user_insert(
    service: Resource, message: Message, email: str, fname: str, lname: str
) -> None:
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
        "primaryEmail": email,
        "password": password,
        "name": {
            "givenName": fname.title(),
            "familyName": lname.title(),
        },
    }
    try:
        service.users().insert(body=body).execute()
        botsend(message, f"ユーザー `{email}` を追加しました")
        # password をユーザーにDMで伝える
        _send_password_on_dm(message, email, password)
    except HttpError as e:
        botsend(message, f"ユーザーの追加に失敗しました\n`{e}`")


def _gadmin_user_delete(service: Resource, message: Message, email: str) -> None:
    """
    指定したユーザーを削除する

    :param service: Google API との接続
    :param email: メールアドレス
    """
    try:
        # 停止中のユーザーのみ削除対象とする
        result = service.users().get(userKey=email).execute()
        if not result["suspended"]:
            botsend(
                message,
                "ユーザーはアクティブなため削除できません\n"
                f"`$gadmin user suspend {email}` でユーザーを停止してから削除してください",
            )
        else:
            service.users().delete(userKey=email).execute()
            botsend(message, f"ユーザー `{email}` を削除しました")
    except HttpError as e:
        botsend(message, f"ユーザーの削除に失敗しました\n`{e}`")


def _gadmin_user_update(
    service: Resource, message: Message, email: str, suspended: bool
) -> None:
    """
    ユーザーの情報を更新する

    :param service: Google API との接続
    :param email: メールアドレス
    :param suspended: ユーザーの状態、True or False
    """
    body = {
        "suspended": suspended,
    }
    try:
        service.users().update(userKey=email, body=body).execute()
        if suspended:
            botsend(message, f"ユーザー `{email}` を停止しました")
        else:
            botsend(message, f"ユーザー `{email}` を再開しました")
    except HttpError as e:
        botsend(message, f"ユーザー情報の更新に失敗しました\n`{e}`")


def _gadmin_user_password_reset(
    service: Resource, message: Message, email: str
) -> None:
    """
    ユーザーのパスワードをリセットする

    :param service: Google API との接続
    :param email: メールアドレス
    """
    # パスワードを生成する
    password = _generate_password()
    body = {
        "password": password,
    }
    try:
        service.users().update(userKey=email, body=body).execute()
        botsend(message, f"ユーザー `{email}` のパスワードをリセットしました")
        # password を実行ユーザーにDMで伝える
        _send_password_on_dm(message, email, password)
    except HttpError as e:
        botsend(message, f"ユーザーパスワードのリセットに失敗しました\n`{e}`")


@respond_to(r"^gadmin\s+user\s+(insert)\s+(\S+)\s+(\S+)\s+(\S+)")
@respond_to(r"^gadmin\s+user\s+(delete|suspend|resume|reset)\s+(\S+)")
def gadmin_user_insert_delete(
    message: Message, command: str, email: str, fname: str = "", lname: str = ""
) -> None:
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
    user = message.body["user"]
    if not _is_admin(user):
        botsend(message, "このコマンドの実行にはAdmin以上の権限が必要です")
        return

    service = _get_service()
    email = _get_default_domain_email(email)

    if command == "insert":
        _gadmin_user_insert(service, message, email, fname, lname)
    elif command == "delete":
        _gadmin_user_delete(service, message, email)
    elif command == "suspend":
        # ユーザーを停止して停止中にする
        _gadmin_user_update(service, message, email, suspended=True)
    elif command == "resume":
        # ユーザーを再開してアクティブにする
        _gadmin_user_update(service, message, email, suspended=False)
    elif command == "reset":
        # ユーザーのパスワードをリセットする
        _gadmin_user_password_reset(service, message, email)


@respond_to(r"^gadmin\s+alias\s+list\s+(.*)")
def gadmin_alias_list(message: Message, email: str) -> None:
    """
    指定したユーザーのエイリアスの一覧を返す

    :param email: メールアドレス
    """

    service = _get_service()
    email = _get_default_domain_email(email)
    try:
        result = service.users().aliases().list(userKey=email).execute()
        msg = ""
        aliases = result.get("aliases", [])
        if aliases:
            msg = f"`{email}` のエイリアス一覧\n"
            msg += ", ".join(f"`{alias['alias']}`" for alias in aliases)
            botsend(message, msg)
        else:
            msg = f"`{email}` のエイリアスはありません"
            botsend(message, msg)
    except HttpError as e:
        botsend(message, f"エイリアスの取得失敗しました\n`{e}`")


def _gadmin_alias_insert(
    service: Resource, message: Message, email: str, alias: str
) -> None:
    """
    指定したユーザーにエイリアスを追加する

    :param service: Google API との接続
    :param email: 追加対象のメールアドレス
    :param alias: エイリアスのメールアドレス
    """
    body = {
        "alias": alias,
    }
    try:
        service.users().aliases().insert(userKey=email, body=body).execute()
        botsend(message, f"`{email}` にエイリアス `{alias}` を追加しました")
    except HttpError as e:
        botsend(message, f"エイリアスの追加に失敗しました\n`{e}`")


def _gadmin_alias_delete(
    service: Resource, message: Message, email: str, alias: str
) -> None:
    """
    指定したユーザーからエイリアスを削除する

    :param service: Google API との接続
    :param email: 追加対象のメールアドレス
    :param alias: エイリアスのメールアドレス
    """
    try:
        service.users().aliases().delete(userKey=email, alias=alias).execute()
        botsend(message, f"`{email}` からエイリアス `{alias}` を削除しました")
    except HttpError as e:
        botsend(message, f"エイリアスの削除に失敗しました\n`{e}`")


@respond_to(r"^gadmin\s+alias\s+(insert|delete)\s+(.*)\s+(.*)")
def gadmin_alias_insert_delete(
    message: Message, command: str, email: str, alias: str
) -> None:
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

    if command == "insert":
        _gadmin_alias_insert(service, message, email, alias)
    elif command == "delete":
        _gadmin_alias_delete(service, message, email, alias)


@respond_to(r"^gadmin\s+group\s+list")
def gadmin_group_list(message: Message) -> None:
    """
    グループの一覧を返す
    """
    service = _get_service()
    groups_list = service.groups().list(domain=DOMAIN).execute()

    count = 0
    msg = ""
    for group in groups_list.get("groups", []):
        email = group["email"]
        name = group["name"]
        member_count = group["directMembersCount"]
        msg += f"- {email} {name}({member_count}ユーザー)\n"
        count += 1
    msg = f"{DOMAIN}ドメインのグループ一覧({count}グループ)\n{msg}"
    botsend(message, msg)


def _gadmin_group_insert(
    message: Message, service: Resource, group: str, name: str
) -> None:
    """
    指定したグループを追加する

    :param service: Google API との接続
    :param group: グループのメールアドレス
    :param name: グループの名前
    """
    body = {
        "name": name,
        "email": group,
    }
    try:
        service.groups().insert(body=body).execute()
    except HttpError as e:
        botsend(message, f"グループの追加に失敗しました\n`{e}`")
        return
    botsend(message, f"`{group}` グループを追加しました")
    botsend(message, f"`$gadmin member insert {group} メールアドレス` コマンドでメンバーを追加してください")


def _gadmin_group_delete(message: Message, service: Resource, group: str) -> None:
    """
    指定したグループを削除する

    :param service: Google API との接続
    :param group: グループのメールアドレス
    """
    try:
        result = service.groups().get(groupKey=group).execute()
        count = result["directMembersCount"]
        if count != "0":
            # メンバーがいる場合は削除できない
            botsend(
                message,
                f"""
`{group}` グループはメンバーがいるので削除できません
`$gadmin member delete {group} メールアドレス` コマンドでメンバーを削除してから実行してください
`$gadmin member list {group}` コマンドでメンバー一覧が確認できます
""",
            )
        else:
            service.groups().delete(groupKey=group).execute()
            botsend(message, f"`{group}` グループを削除しました")
    except HttpError as e:
        botsend(message, f"グループの削除に失敗しました\n`{e}`")
        return


@respond_to(r"^gadmin\s+group\s+(insert)\s+(.*)\s+(.*)")
@respond_to(r"^gadmin\s+group\s+(delete)\s+(.*)")
def gadmin_group_insert_delete(
    message: Message, command: str, group: str, name: str = ""
) -> None:
    """
    指定したグループを追加/削除する

    - `$gadmin group insert (group) (name)`
    - `$gadmin group delete (group)`

    :param group: グループのメールアドレスまたは@の前の部分
    :param name: グループの名前
    """
    # コマンドを実行したユーザーのIDを取得
    user = message.body["user"]
    if not _is_admin(user):
        botsend(message, "このコマンドの実行にはAdmin以上の権限が必要です")
        return

    # グループ、メンバー情報の前処理
    group = _get_default_domain_email(group)
    service = _get_service()
    if command == "insert":
        _gadmin_group_insert(message, service, group, name)
    elif command == "delete":
        _gadmin_group_delete(message, service, group)


@respond_to(r"^gadmin\s+member\s+list\s+(.*)")
def gadmin_member_list(message: Message, group: str) -> None:
    """
    グループのメンバー一覧を返す

    :param key: グループのメールアドレス(@の前の部分)
    """
    service = _get_service()
    group = _get_default_domain_email(group)
    try:
        members_list = service.members().list(groupKey=group).execute()
    except HttpError:
        botsend(message, f"`{group}` に合致するグループはありません")
        return

    count = 0
    msg = ""
    for member in members_list.get("members", []):
        email = member["email"]
        msg += f"- {email}\n"
        count += 1
    msg = f"*{group}* グループのメンバー({count}ユーザー)\n{msg}"
    botsend(message, msg)


def _gadmin_member_insert(
    message: Message, service: Resource, group: str, emails: list[str]
) -> None:
    """
    指定したメンバーを指定したグループに追加する

    :param service: Google API との接続
    :param group: グループのメールアドレス
    :param mail: 追加/削除するメンバーのメールアドレス
    """

    for email in emails:
        body = {
            "email": email,
        }
        try:
            service.members().insert(groupKey=group, body=body).execute()
            botsend(message, f"`{group}` グループに `{email}` を追加しました")
        except HttpError as e:
            # TODO: グループが間違っている場合とメンバーのエラーの場合わけ
            botsend(message, f"メンバーの追加に失敗しました\n`{e}`")


def _gadmin_member_delete(
    message: Message, service: Resource, group: str, emails: list[str]
) -> None:
    """
    指定したメンバーを指定したグループから削除する

    :param service: Google API との接続
    :param group: グループのメールアドレス
    :param mail: 追加/削除するメンバーのメールアドレス
    """
    for email in emails:

        try:
            service.members().delete(groupKey=group, memberKey=email).execute()
            botsend(message, f"`{group}` グループから `{email}` を削除しました")
        except HttpError as e:
            # TODO: グループが間違っている場合とメンバーのエラーの場合わけ
            botsend(message, f"メンバーの削除に失敗しました\n`{e}`")


@respond_to(r"^gadmin\s+member\s+(insert|delete)\s+(\S*)\s+(.*)")
def gadmin_member_insert_delete(
    message: Message, command: str, group: str, email: str
) -> None:
    """
    指定したメンバーを指定したグループに追加/削除する

    - `$gadmin member insert (group) (email...)`
    - `$gadmin member delete (group) (email...)`

    :param group: グループのメールアドレスまたは@の前の部分
    :param mail: 追加/削除するメンバーのメールアドレス
    """
    # コマンドを実行したユーザーのIDを取得
    user = message.body["user"]
    if not _is_admin(user):
        botsend(message, "このコマンドの実行にはAdmin以上の権限が必要です")
        return

    # グループ、メンバー情報の前処理
    emails = []
    for email in email.split():
        email = _remove_email_link(email)
        if "@" in email:
            emails.append(email)
    group = _get_default_domain_email(group)
    service = _get_service()

    # 対象となるメールアドレスがある場合のみ処理する
    if emails:
        if command == "insert":
            _gadmin_member_insert(message, service, group, emails)
        elif command == "delete":
            _gadmin_member_delete(message, service, group, emails)
    else:
        botsend(message, "正しいメールアドレスを指定してください")


@respond_to(r"^gadmin\s+help")
def gadmin_help(message: Message) -> None:
    """
    コマンドのヘルプを表示
    """
    botsend(message, HELP)
