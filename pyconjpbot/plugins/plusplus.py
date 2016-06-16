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

@listen_to(r'(@?[^@]*[^:+-]):?\s*(\+\+|--)')
def plusplus(message, target, plusplus):
    """
    指定された名前に対して ++ または -- する
    takanory++
    takanory:++
    takanory: ++
    @takanory++
    @takanory:++
    @takanory: ++
    """
    import pdb
    # 名前が <@userid> でくる
    pdb.set_trace()
    message.send('name: {}, plusplus: {}'.format(target, plusplus))
