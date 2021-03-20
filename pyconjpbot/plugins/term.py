import random
from datetime import datetime

from slackbot.bot import respond_to

from ..botmessage import botsend, botwebapi
from .term_model import Response, Term

# すでに存在するコマンドは無視する
RESERVED = (
    "drive",
    "manual",
    "jira",
    "wikipedia",
    "plusplus",
    "translate",
    "翻訳",
    "weather",
    "天気",
    "term",
    "shuffle",
    "help",
    "choice",
    "ping",
    "version",
    "random",
    "cal",
    "google",
    "image",
    "map",
    "gadmin",
    "github",
    "suddendeath",
    "pycamp",
    "lgtm",
)

# コマンド一覧を初期化
commands = {term.command for term in Term.select()}


@respond_to(r"^term\s+([\w-]+)$")
@respond_to(r"^term\s+create\s+([\w-]+)$")
@respond_to(r"^term\s+add\s+([\w-]+)$")
def term_create(message, command):
    """
    指定されたコマンドを生成する
    """
    if command in ("list", "help"):
        return

    # コマンドは小文字に統一
    command = command.lower()
    # 予約語の場合は実行しない
    if command in RESERVED:
        botsend(message, f"コマンド `${command}` は予約語なので登録できません")
        return

    creator = message.body["user"]
    term, created = Term.get_or_create(command=command, creator=creator)
    if not created:
        # すでに登録してあるコマンドは登録しない
        botsend(message, f"コマンド `${command}` はすでに登録されています")

    else:
        msg = f"コマンド `${command}` を作成しました。\n"
        msg += f"`${command} add (レスポンス)` でレスポンスを追加できます"
        botsend(message, msg)

        # コマンド一覧の set に追加
        commands.add(command)


@respond_to(r"^term\s+(drop|del|delete)\s+([\w-]+)$")
def term_drop(message, subcommand, command):
    """
    指定されたコマンドを消去する
    """
    # コマンドは小文字に統一
    command = command.lower()

    # コマンドの存在チェック
    if not _available_command(message, command):
        return

    # 用語コマンドと応答をまとめて削除
    term = Term.get(command=command)
    term.delete_instance(recursive=True)
    term.save()

    # コマンド一覧の set から削除
    commands.remove(command)
    botsend(message, f"コマンド `${command}` を消去しました")


def _create_attachments_for_list(pretext, data, command=True):
    """
    指定されたリストの一覧を message.send_webapi で送信するための
    attachments を生成する
    """
    if command:
        # ['foo', 'bar', 'baz'] -> '`$far`, `$bar`, `$baz`'
        list_text = ", ".join([f"`${x}`" for x in data])
    else:
        list_text = "\n".join([x for x in data])
    attachments = [
        {
            "pretext": pretext,
            "text": list_text,
            "mrkdwn_in": ["pretext", "text"],
        }
    ]
    return attachments


@respond_to(r"^term\s+search\s+([\w-]+)$")
def term_search(message, keyword):
    """
    指定したキーワードを含む用語コマンドの一覧を返す
    """
    pretext = f"`{keyword}` を含む用語コマンドの一覧です"
    data = []
    for command in sorted(commands):
        if keyword in command:
            data.append(command)
    attachments = _create_attachments_for_list(pretext, data)
    botwebapi(message, attachments)


@respond_to(r"^term\s+list$")
def term_list(message):
    """
    現在使用可能な用語コマンドの一覧を返す
    """
    pretext = "用語コマンドの一覧です"
    attachments = _create_attachments_for_list(pretext, sorted(commands))
    botwebapi(message, attachments)


def _available_command(message, command):
    """
    指定されたコマンドが有効化どうかを返す
    """
    result = True

    if command in RESERVED:
        result = False
    elif command not in commands:
        botsend(message, f"コマンド `${command}` は登録されていません")
        result = False

    return result


def _send_markdown_text(message, text):
    """
    指定されたtextをmarkdown形式で送信する
    """
    attachments = [
        {
            "pretext": text,
            "mrkdwn_in": ["pretext"],
        }
    ]
    botwebapi(message, attachments)


@respond_to(r"^([\w-]+)$")
def return_response(message, command):
    """
    用語コマンドに登録されている応答をランダムに返す
    """
    if not _available_command(message, command):
        return

    response_set = Term.get(command=command).response_set
    if len(response_set) == 0:
        msg = f"コマンド `${command}` には応答が登録されていません\n"
        msg += f"`${command} add (レスポンス)` で応答を登録してください"
        botsend(message, msg)
    else:
        response = random.choice(response_set)
        _send_markdown_text(message, response.text)


@respond_to(r"^([\w-]+)\s+(.*)")
def response(message, command, params):
    """
    用語コマンドの処理をする
    """
    if not _available_command(message, command):
        return

    data = params.split(maxsplit=1)
    subcommand = data[0]
    try:
        if subcommand == "pop":
            # 最後に登録された応答を削除
            pop_response(message, command)
        elif subcommand == "list":
            # 応答の一覧を返す
            get_responses(message, command)
        elif subcommand == "search":
            # 応答を検索
            search_responses(message, command, data[1])
        elif subcommand in ("del", "delete", "remove"):
            # 応答を削除
            del_response(message, command, data[1])
        elif subcommand == "add":
            # 応答を追加
            add_response(message, command, data[1])
        else:
            # サブコマンドが存在しない場合も追加
            add_response(message, command, params)
    except IndexError:
        # ヘルプを返す
        term_help(message)
        pass


def _exist_response(command, text):
    """
    指定されたコマンドに応答が登録されているかを調べて返す
    """
    term = Term.get(command=command)
    count = (
        Response.select().where(Response.term == term, Response.text == text).count()
    )
    if count == 0:
        return False
    else:
        return True


def add_response(message, command, text):
    """
    用語コマンドに応答を追加する
    """

    # 登録済かどうかを確認する
    if _exist_response(command, text):
        reply = f"コマンド `${command}` に「{text}」は登録済みです"
        _send_markdown_text(message, reply)
        return

    term = Term.get(command=command)
    creator = message.body["user"]
    # 用語を登録する
    resp, created = Response.get_or_create(
        term=term, text=text, creator=creator, created=datetime.now()
    )
    resp.save()
    text = f"コマンド `${command}` に「{text}」を追加しました"
    _send_markdown_text(message, text)


def del_response(message, command, text):
    """
    用語コマンドから応答を削除する
    """
    term = Term.get(command=command)
    try:
        response = Response.get(term=term, text=text)
    except Response.DoesNotExist:
        reply = f"コマンド `${command}` に「{text}」は登録されていません"
        _send_markdown_text(message, reply)
        return

    # 応答を削除する
    response.delete_instance()

    reply = f"コマンド `${command}` から「{text}」を削除しました"
    _send_markdown_text(message, reply)


def pop_response(message, command):
    """
    用語コマンドで最後に登録された応答を削除する
    """
    response_set = Term.get(command=command).response_set
    # 応答が登録されていない
    if len(response_set) == 0:
        msg = f"コマンド `${command}` には応答が登録されていません\n"
        msg += f"`${command} add (レスポンス)` で応答を登録してください"
        botsend(message, msg)
        return

    last_response = response_set.order_by(Response.created.desc())[0]
    text = last_response.text
    last_response.delete_instance()

    reply = f"コマンド `${command}` から「{text}」を削除しました"
    _send_markdown_text(message, reply)


def search_responses(message, command, keyword):
    """
    用語コマンドに登録されている応答のうち、キーワードにマッチするものを返す
    """
    term = Term.get(command=command)
    pat = f"%{keyword}%"
    responses = Response.select().where(term == term, Response.text ** pat)

    if len(responses) == 0:
        botsend(message, f"コマンド `${command}` に `{keyword}` を含む応答はありません")
    else:
        pretext = f"コマンド `${command}` の `{keyword}` を含む応答は {len(responses)} 件あります\n"
        data = [x.text for x in responses]
        attachments = _create_attachments_for_list(pretext, data, False)
        botwebapi(message, attachments)


def get_responses(message, command):
    """
    用語コマンドに登録されている応答の一覧を返す
    """
    response_set = Term.get(command=command).response_set
    if len(response_set) == 0:
        msg = f"コマンド `${command}` には応答が登録されていません\n"
        msg += f"`${command} add (レスポンス)` で応答を登録してください"
        botsend(message, msg)
    else:
        pretext = f"コマンド `${command}` の応答は {len(response_set)} 件あります\n"
        data = [x.text for x in response_set]
        attachments = _create_attachments_for_list(pretext, data, False)
        botwebapi(message, attachments)


@respond_to(r"term\s+help")
def term_help(message):
    """
    term pluginのヘルプを返す
    """
    botsend(
        message,
        """- `$term (用語)`: 用語コマンドを作成する
- `$term create (用語)`: 用語コマンドを作成する
- `$term drop (用語)`: 用語コマンドを消去する
- `$term search (キーワード)`: キーワードを含む用語コマンドの一覧を返す
- `$term list`: 用語コマンドの一覧を返す

- `$(用語)`: 用語コマンドに登録してある応答からランダムに一つ返す
- `$(用語) add (応答)`: 用語コマンドに応答を追加する
- `$(用語) del (応答)`: 用語コマンドから応答を削除する
- `$(用語) pop`: 用語コマンドの最後に登録した応答を削除する
- `$(用語) list`: 用語コマンドの応答一覧を返す
- `$(用語) search (キーワード)`: 用語コマンドのうちキーワードを含む応答一覧を返す
```
> $term create 酒
コマンド `$酒` を作成しました。
`$酒 add (レスポンス)` でレスポンスを追加できます
> $酒 add ビール
コマンド `$酒` に `ビール` を追加しました
> $酒 add ワイン
コマンド `$酒` に `ワイン` を追加しました
> $酒
ビール
```
""",
    )
