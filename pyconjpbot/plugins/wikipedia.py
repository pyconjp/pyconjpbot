import wikipedia
from slackbot.bot import respond_to
from slackbot.dispatcher import Message

from ..botmessage import botsend, botwebapi


@respond_to(r"^wikipedia(\s+-\w+)?\s+(.*)")
def wikipedia_page(message: Message, option: str, query: str) -> None:
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
    except Exception:
        botsend(message, f"指定された言語 `{lang}` は存在しません")
        return

    # get first result
    if results:
        page = wikipedia.page(results[0])

        attachments = [
            {
                "fallback": f"Wikipedia: {page.title}",
                "pretext": f"Wikipedia: <{page.url}|{page.title}>",
                "text": page.summary,
            }
        ]
        botwebapi(message, attachments)
    else:
        botsend(message, f"`{query}` に該当するページはありません")


@respond_to(r"^wikipedia\s+help")
def wikipedia_help(message: Message) -> None:
    botsend(
        message,
        """`$wikipedia keywords`: Wikipedia で指定されたページを返す
`$wikipedia -en keywords`: Wikipedia で指定された言語(en等)のページを返す
""",
    )
