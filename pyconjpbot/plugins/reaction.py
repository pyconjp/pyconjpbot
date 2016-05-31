import re

from slackbot.bot import listen_to

@listen_to('肉')
@listen_to('meat', re.IGNORECASE)
def react_niku(message):
    message.react('meat_on_bone')

@listen_to('酒')
def react_niku(message):
    message.react('sake')
    
@listen_to('ビール')
@listen_to('beer', re.IGNORECASE)
def react_niku(message):
    message.react('beers')
    
@listen_to('すし')
@listen_to('寿司')
@listen_to('sushi')
def react_niku(message):
    message.react('sushi')
    
@listen_to('ピザ')
@listen_to('pizza', re.IGNORECASE)
def react_niku(message):
    message.react('pizza')
    
@listen_to('カレーメシ')
def react_niku(message):
    message.react('curry')
    message.react('boom')
    
