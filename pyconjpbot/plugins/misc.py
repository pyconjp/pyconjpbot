import json
import random

from slackbot.bot import respond_to, listen_to
import git

@respond_to('^help$')
def help(message):
    """
    helpページのURLを返す
    """
    message.send('ヘルプはこちら→ https://github.com/pyconjp/pyconjpbot#commands')

@respond_to('shuffle (.*)')
def shuffle(message, words):
    """
    指定したキーワードをシャッフルして返す
    """
    words = words.split()
    if len(words) == 1:
        message.send('キーワードを複数指定してください\n`$shuffle word1 word2...`')
    else:
        random.shuffle(words)
        message.send(' '.join(words))

@respond_to('choice (.*)')
def choice(message, words):
    """
    指定したキーワードから一つを選んで返す
    """
    words = words.split()
    if len(words) == 1:
        message.send('キーワードを複数指定してください\n`$choice word1 word2...`')
    else:
        message.send(random.choice(words))
        
@respond_to('^ping$')
def help(message):
    """
    pingに対してpongで応答する
    """
    message.reply('pong')

@respond_to('^version$')
def help(message):
    """
    バージョン情報を返す
    """
    obj = git.Repo('').head.object
    url = "https://github.com/pyconjp/pyconjpbot/commit/{}".format(obj.hexsha)
    text = "<{}|{}> {} - {}({})".format(url, obj.hexsha[:6], obj.summary,
                                       obj.committer.name, obj.committed_datetime)
    attachments = [{
        'pretext': text,
    }]
    message.send_webapi('', json.dumps(attachments))

