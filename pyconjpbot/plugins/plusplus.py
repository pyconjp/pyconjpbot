from slackbot.bot import listen_to

@listen_to(r'@?([^@]*[^-:]):?\s+(\+\+|--)')
def plusplus(message, target, plusplus):
    """
    指定された名前に対して ++ または -- する
    """
    message.send('{} {}'.format(target, plusplus))
