import re
from unicodedata import east_asian_width

from slackbot.bot import respond_to
from slackbot.dispatcher import Message

from ..botmessage import botsend


def _message_length(message: str) -> int:
    """
    メッセージの長さを返す
    """
    length = 0
    for char in message:
        width = east_asian_width(char)
        if width in ("W", "F", "A"):
            length += 2
        elif width in ("Na", "H"):
            length += 1

    return length


@respond_to(r"^suddendeath$")
@respond_to(r"^suddendeath\s+(.*)")
def suddendeath(message: Message, words: str = "突然の死") -> None:
    """
    突然の死のメッセージを返す
    """
    if words == "help":
        return

    # slack の絵文字っぽいパターンは全角文字と同じ長さとする
    words_for_length = re.sub(r":[-+\w]+:", "蛇", words)
    length = _message_length(words_for_length)
    soft_hyphen = b"\\u00AD".decode("unicode-escape")

    header = soft_hyphen + "＿" + "人" * (length // 2 + 2) + "＿"
    footer = soft_hyphen + "￣" + "Y^" * (length // 2) + "Y￣"
    middle = soft_hyphen + "＞　" + words + "　＜"

    botsend(message, "\n".join([header, middle, footer]))


@respond_to(r"^suddendeath\s+help")
def suddendeath_help(message: Message) -> None:
    botsend(
        message,
        """- `$suddendeath`: 突然の死のメッセージを返す
- `$suddendeath words`: words を使って突然の死のメッセージを返す
""",
    )
