import random

from slackbot.bot import listen_to
from slackbot import settings
import slacker

from .plusplus_model import Plusplus

def _get_user_name(user_id):
    """
    指定された Slack の user_id に対応する username を返す

    Slacker で users.list API を呼び出す
    - https://github.com/os/slacker
    - https://api.slack.com/methods/users.info
    """
    webapi = slacker.Slacker(settings.API_TOKEN)
    response = webapi.users.info(user_id)
    if response.body['ok']:
        return response.body['user']['name']
    else:
        return ''

def _update_count(message, target, plusplus):
    """
    指定ユーザーのカウンターを更新する
    """
    plus, created = Plusplus.get_or_create(name=target, defaults={'counter': 0})
    
    if plusplus == '++':
        plus.counter += 1
        msg = 'leveled up!'
    else:
        plus.counter -= 1
        msg = 'leveled down!'
    plus.save()

    message.send('{} {} (通算: {})'.format(target, msg, plus.counter))
    
@listen_to(r'^<@(\w+)>:?\s*(\+\+|--)($|[^+-])')
def mention_plusplus(message, user_id, plusplus, after):
    """
    mentionされたユーザーに対して ++ または -- する
    """
    target = _get_user_name(user_id)
    _update_count(message, target, plusplus)
    
@listen_to(r'^(\w+):?\s*(\+\+|--)($|[^+-])')
def plusplus(message, target, plusplus, after):
    """
    指定された名前に対して ++ または -- する

    takanory++
    takanory:++
    takanory: ++
    日本語++
    """
    _update_count(message, target, plusplus)
