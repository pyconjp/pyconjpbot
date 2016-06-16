from slackbot.bot import listen_to
from slackbot import settings
import slacker

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

@listen_to(r'^<@(\w+)>:?\s*(\+\+|--)($|[^+-])')
def mention_plusplus(message, user_id, plusplus, after):
    """
    mentionされたユーザーに対して ++ または -- する
    """
    target = _get_user_name(user_id)
    message.send('name: {}, plusplus: {}'.format(target, plusplus))
    
@listen_to(r'^(\w+):?\s*(\+\+|--)($|[^+-])')
def plusplus(message, target, plusplus, after):
    """
    指定された名前に対して ++ または -- する

    takanory++
    takanory:++
    takanory: ++
    日本語++
    """

    message.send('name: {}, plusplus: {}'.format(target, plusplus))
