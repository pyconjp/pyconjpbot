from urllib.parse import quote_plus

from slackbot.bot import respond_to, listen_to

# マニュアルのURL
URL = 'http://manual.pycon.jp/'

@listen_to('^manual$')
@listen_to('^マニュアル$')
def manual(message):
    """
    マニュアルのURLを返す
    """
    message.send('PyCon JP 運営マニュアル {}'.format(URL))

@listen_to('^manual (.*)')
def manual_search(message, query):
    """
    マニュアルをキーワード検索したURLを返す
    """
    if query != 'help':
        message.send('{}search.html?q={}'.format(URL, quote_plus(query)))

@listen_to('^manual help$')
def manual_help(message):
    """
    マニュアルコマンドのヘルプを返す
    """
    message.send('''- `manual`: マニュアルのURLを返す
- `manual keywords`: マニュアルを指定キーワード検索する''')
