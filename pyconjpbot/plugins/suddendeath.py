from unicodedata import east_asian_width
import re

from slackbot.bot import respond_to


def _message_length(message):
    """
    メッセージの長さを返す
    """
    length = 0
    for char in message:
        width = east_asian_width(char)
        if width in ('W', 'F', 'A'):
            length += 2
        elif width in ('Na', 'H'):
            length += 1

    return length

@respond_to('^suddendeath$')
@respond_to('^suddendeath\s+(.*)')
def suddendeath(message, words='突然の死'):
    """
    突然の死のメッセージを返す
    """
    if words == 'help':
        return

    # slack の絵文字っぽいパターンは全角文字と同じ長さとする
    words_for_length = re.sub(':[-+\w]+:', '蛇', words)
    length = _message_length(words_for_length)

    header = '＿' + '人' * (length // 2 + 2) + '＿'
    footer = '￣' + 'Y^' * (length // 2) + 'Y￣'
    middle = "＞　" + words + "　＜"

    message.send("\n".join([header, middle, footer]))

@respond_to('^suddendeath\s+help')
def suddendeath_help(message):
    message.send('''- `$suddendeath`: 突然の死のメッセージを返す
- `$suddendeath words`: words を使って突然の死のメッセージを返す
''')
