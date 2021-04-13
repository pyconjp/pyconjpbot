import random

import slacker
from slackbot import settings
from slackbot.bot import listen_to, respond_to
from slackbot.dispatcher import Message

from ..botmessage import botsend, botwebapi
from .plusplus_model import Plusplus

PLUS_MESSAGE = (
    "leveled up!",
    "レベルが上がりました!",
    "やったね",
    "(☝՞ਊ ՞)☝ウェーイ",
)

MINUS_MESSAGE = (
    "leveled down.",
    "レベルが下がりました",
    "ドンマイ!",
    "(´・ω・｀)",
)


def _get_user_name(user_id: str) -> str:
    """
    指定された Slack の user_id に対応する username を返す

    Slacker で users.list API を呼び出す
    - https://github.com/os/slacker
    - https://api.slack.com/methods/users.info
    """
    webapi = slacker.Slacker(settings.API_TOKEN)
    response = webapi.users.info(user_id)
    if response.body["ok"]:
        return response.body["user"]["name"]
    else:
        return ""


def _update_count(message: Message, target: str, plusplus: str) -> None:
    """
    指定ユーザーのカウンターを更新する
    """
    target = target.lower()
    # 1文字の対象は無視する
    if len(target) < 2:
        return
    plus, created = Plusplus.get_or_create(name=target, defaults={"counter": 0})

    if plusplus == "++":
        plus.counter += 1
        msg = random.choice(PLUS_MESSAGE)
    else:
        plus.counter -= 1
        msg = random.choice(MINUS_MESSAGE)
    plus.save()

    botsend(message, f"{target} {msg} (通算: {plus.counter})")


@listen_to(r"^(.*):?\s*(\+\+|--)")
def multi_plusplus(message: Message, targets: str, plusplus: str) -> None:
    """
    指定された複数の名前に対して ++ する

    takanory terada++
    takanory  terada  ++
    takanory   terada: ++
    日本語++
    takanory  @terada++ コメント
    """
    for target in targets.split():
        # user_id(<@XXXXXX>)をユーザー名に変換する
        if target.startswith("<@"):
            user_id = target[2:-1]  # user_idを取り出す
            target = _get_user_name(user_id)
        # 先頭に @ があったら削除する
        if target.startswith("@"):
            target = target[1:]
        _update_count(message, target, plusplus)


@respond_to(r"^plusplus\s+(del|delete)\s+(\S+)")
def plusplus_delete(message: Message, subcommand: str, name: str) -> None:
    """
    指定された名前を削除する
    カウントが10未満のもののみ削除する
    """

    try:
        plus = Plusplus.get(name=name)
    except Plusplus.DoesNotExist:
        message.send(f"`{name}` という名前は登録されていません")
        return

    if abs(plus.counter) > 10:
        botsend(message, f"`{name}` のカウントが多いので削除を取り消しました(count: {plus.counter})")
        return

    plus.delete_instance()
    message.send(f"`{name}` を削除しました")


@respond_to(r"^plusplus\s+rename\s+(\S+)\s+(\S+)")
def plusplus_rename(message: Message, old: str, new: str) -> None:
    """
    指定された old から new に名前を変更する
    """
    try:
        oldplus = Plusplus.get(name=old)
    except Plusplus.DoesNotExist:
        botsend(message, f"`{old}` という名前は登録されていません")
        return

    newplus, created = Plusplus.get_or_create(name=new, counter=oldplus.counter)
    if not created:
        # すでに存在している
        message.send(f"`{new}` という名前はすでに登録されています")
        return

    # 入れ替える
    oldplus.delete_instance()
    botsend(message, f"`{old}` から `{new}` に名前を変更しました(count: {oldplus.counter})")


@respond_to(r"^plusplus\s+merge\s+(\S+)\s+(\S+)")
def plusplus_merge(message: Message, old: str, new: str) -> None:
    """
    指定された old と new を一つにまとめる
    """
    try:
        oldplus = Plusplus.get(name=old)
    except Plusplus.DoesNotExist:
        botsend(message, f"`{old}` という名前は登録されていません")
        return

    try:
        newplus = Plusplus.get(name=new)
    except Plusplus.DoesNotExist:
        botsend(message, f"`{new}` という名前は登録されていません")
        return

    oldcount = oldplus.counter
    newcount = newplus.counter

    # 値を統合する
    newplus.counter += oldplus.counter
    newplus.save()
    oldplus.delete_instance()

    botsend(
        message,
        (
            f"`{old}` を `{new}` に統合しました"
            f"(count: {oldcount} + {newcount} = {newplus.counter})"
        ),
    )


@respond_to(r"^plusplus\s+search\s+(\S+)")
def plusplus_search(message: Message, keyword: str) -> None:
    """
    指定されたキーワードを含む名前とカウントの一覧を返す
    """
    pattern = f"%{keyword}%"
    pluses = Plusplus.select().where(Plusplus.name ** pattern)

    if len(pluses) == 0:
        botsend(message, f"`{keyword}` を含む名前はありません")
    else:
        pretext = f"`{keyword}` を含む名前とカウントの一覧です\n"
        text = ""
        for plus in pluses:
            text += f"- {plus.name}(count: {plus.counter})\n"
        attachments = [
            {
                "pretext": pretext,
                "text": text,
                "mrkdwn_in": ["pretext", "text"],
            }
        ]
        botwebapi(message, attachments)


@respond_to(r"^plusplus\s+help+")
def plusplus_help(message: Message) -> None:
    """
    ヘルプメッセージを返す
    """
    botsend(
        message,
        """- `名前1 名前2++`: 指定された名前に +1 カウントする
- `名前1 名前2--`: 指定された名前に -1 カウントする
- `$plusplus search (キーワード)`: 名前にキーワードを含む一覧を返す
- `$plusplus delete (名前)`: カウントを削除する(カウント10未満のみ)
- `$plusplus rename (変更前) (変更後)`: カウントする名前を変更する
- `$plusplus merge (統合元) (統合先)`: 2つの名前のカウントを統合先の名前にまとめる
""",
    )
