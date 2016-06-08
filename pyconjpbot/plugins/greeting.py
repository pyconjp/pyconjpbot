"""
あいさつPlugin
"""

from random import choice

from slackbot.bot import listen_to

@listen_to('おはよう|お早う')
def morning(message):
    replies = (
        'おはよう',
        'おはよー',
        'おはようございます',
    )
    message.reply(choice(replies))
    
@listen_to('こんにち[はわ]')
def noon(message):
    replies = (
        'こんにちは',
        'ちーっす',
        'こんにちは、元気ですかー?',
    )
    message.reply(choice(replies))

@listen_to('いってきま|行ってきま')
def go(message):
    replies = (
        'いってらっしゃい',
        'いってらっしゃーい',
        'いってらっしゃ～い',
        'いってら',
    )
    message.reply(choice(replies))

@listen_to('眠た?い|ねむた?い|寝る|寝ます')
def night(message):
    replies = (
        'おやすみなさい',
        'おやす',
        'おやすー',
    )
    message.reply(choice(replies))
