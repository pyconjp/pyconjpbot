import random

from slackbot.bot import respond_to, listen_to

@respond_to('help$')
def help(message):
    message.send('ヘルプはこちら→ https://github.com/pyconjp/pyconjpbot#commands')

@respond_to('shuffle (.*)')
def shuffle(message, words):
    words = words.split()
    if len(words) == 1:
        message.send('キーワードを複数指定してください\n`$shuffle word1 word2...`')
    else:
        random.shuffle(words)
        message.send(' '.join(words))

@respond_to('choice (.*)')
def choice(message, words):
    words = words.split()
    if len(words) == 1:
        message.send('キーワードを複数指定してください\n`$choice word1 word2...`')
    else:
        message.send(random.choice(words))
        
