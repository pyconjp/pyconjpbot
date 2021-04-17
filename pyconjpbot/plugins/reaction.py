from __future__ import annotations

import re

from slackbot.bot import listen_to
from slackbot.dispatcher import Message
from slacker import Error

# リアクション対象のキーワードと絵文字
REACTION = {
    ("肉", "meat"): "meat_on_bone",
    "カレーメシ": ["curry", "boom"],
    ("ピザ", "pizza"): "pizza",
    ("sushi", "寿司", "おすし"): "sushi",
    "酒": "sake",
    ("ビール", "beer"): "beer",
    "さくさく": "panda_face",
    "お茶": "tea",
    ("コーヒー", "coffee"): "coffee",
    "ケーキ": "cake",
    ("ラーメン", "ramen"): "ramen",
}


def _react(message: Message, emojis: list[str]) -> None:
    """
    指定された emoji を reaction で返す
    """
    for emoji in emojis:
        try:
            message.react(emoji)
        except Error as error:
            # 同じリアクションをすると例外が発生するので、無視する
            if error.args[0] == "already_reacted":
                pass
            else:
                raise


@listen_to(".")
def reaction(message: Message) -> None:
    """
    メッセージの中にリアクションする文字列があれば、emojiでリアクションする
    """
    # テキスト全体をとりだす
    text = message.body["text"].lower()
    for words, emojis in REACTION.items():
        if isinstance(words, str):
            words = (words,)
        # 正規表現で指定した単語が存在するかチェックする
        if re.search("|".join(words), text):
            if isinstance(emojis, str):
                emojis = [emojis]
            _react(message, list(emojis))
