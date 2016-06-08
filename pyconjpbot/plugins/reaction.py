import re

from slackbot.bot import listen_to
from slacker import Error

def _react(message, emoji):
    try:
        message.react(emoji)
    except Error as error:
        # 同じリアクションをすると例外が発生するので、無視する
        if error.args[0] == 'already_reacted':
            pass
        else:
            raise

@listen_to('肉')
@listen_to('meat', re.IGNORECASE)
def react_niku(message):
    _react(message, 'meat_on_bone')

@listen_to('酒')
def react_niku(message):
    _react(message, 'sake')
    
@listen_to('ビール')
@listen_to('beer', re.IGNORECASE)
def react_niku(message):
    _react(message, 'beers')
    
@listen_to('すし')
@listen_to('寿司')
@listen_to('sushi')
def react_niku(message):
    _react(message, 'sushi')
    
@listen_to('ピザ')
@listen_to('pizza', re.IGNORECASE)
def react_niku(message):
    _react(message, 'pizza')
    
@listen_to('カレーメシ')
def react_niku(message):
    _react(message, 'curry')
    _react(message, 'boom')
    
@listen_to('さくさく')
def react_niku(message):
    _react(message, 'panda_face')
    
