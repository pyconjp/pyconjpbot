"""
あいさつPlugin
"""

from random import choice

from slackbot.bot import listen_to
from slackbot.dispatcher import Message

from ..botmessage import botreply


@listen_to("おはよう|お早う")
def morning(message: Message) -> None:
    replies = (
        "おはよう",
        "おはよー",
        "おはようございます",
    )
    botreply(message, choice(replies))


@listen_to("こんにち[はわ]")
def noon(message: Message) -> None:
    replies = (
        "こんにちは",
        "ちーっす",
        "こんにちは、元気ですかー?",
    )
    botreply(message, choice(replies))


@listen_to("いってきま|行ってきま")
def go(message: Message) -> None:
    replies = (
        "いってらっしゃい",
        "いってらっしゃーい",
        "いってらっしゃ～い",
        "いってら",
    )
    botreply(message, choice(replies))


@listen_to("眠た?い|ねむた?い|寝る|寝ます")
def night(message: Message) -> None:
    replies = (
        "おやすみなさい",
        "おやす",
        "おやすー",
    )
    botreply(message, choice(replies))
