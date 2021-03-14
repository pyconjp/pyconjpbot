import wikipedia
from slackbot.bot import respond_to

from ..botmessage import botsend, botwebapi


@respond_to(r"^wikipedia(\s+-\w+)?\s+(.*)")
def wikipedia_page(message, option, query):
    """
    Wikipediaで検索した結果を返す
    """
    if query == "help":
        return

    # set language
    lang = "ja"
    if option:
        _, lang = option.split("-")
    wikipedia.set_lang(lang)

    try:
        # search with query
        results = wikipedia.search(query)
    except:
        botsend(message, "指定された言語 `{}` は存在しません".format(lang))
        return

    # get first result
    if results:
        page = wikipedia.page(results[0])

        attachments = [
            {
                "fallback": "Wikipedia: {}".format(page.title),
                "pretext": "Wikipedia: <{}|{}>".format(page.url, page.title),
                "text": page.summary,
            }
        ]
        botwebapi(message, attachments)
    else:
        botsend(message, "`{}` に該当するページはありません".format(query))


@respond_to(r"^wikipedia\s+help")
def wikipedia_help(message):
    botsend(
        message,
        """`$wikipedia keywords`: Wikipedia で指定されたページを返す
`$wikipedia -en keywords`: Wikipedia で指定された言語(en等)のページを返す
""",
    )
