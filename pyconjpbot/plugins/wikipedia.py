import json

from slackbot.bot import respond_to, listen_to
import wikipedia

@respond_to('wikipedia (-\w+)? (.*)')
def wikipedia_page(message, lang, query):
    """
    Wikipediaで検索した結果を返す
    """
    if query == 'help':
        return
    
    # set language
    if lang:
        wikipedia.set_lang(lang[1:])
    else:
        wikipedia.set_lang('ja')

    try:
        # search with query
        results = wikipedia.search(query)
    except:
        message.send('指定された言語 `{}` は存在しません'.format(lang))
        return
    
    # get first result
    if results:
        page = wikipedia.page(results[0])

        attachments = [{
            'fallback': 'Wikipedia: {}'.format(page.title),
            'pretext': 'Wikipedia: <{}|{}>'.format(page.url, page.title),
            'text': page.summary,
        }]
        message.send_webapi('', json.dumps(attachments))
    else:
        message.send('`{}` に該当するページはありません'.format(query))
    
@respond_to('wikipedia help')
def wikipedia_help(message):
    message.send('''`$wikipedia keywords`: Wikipedia で指定されたページを返す
`$wikipedia -en keywords`: Wikipedia で指定された言語(en等)のページを返す
''')
