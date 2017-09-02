import xml.etree.ElementTree as ET

from slackbot import settings
from slackbot.bot import respond_to

import requests
from langdetect import detect


def get_access_token(key):
    """
    Cognitive ServiceでAPI認証を行い、トークンを取得する

    参考: http://beachside.hatenablog.com/entry/2017/01/27/123000

    :params key: APIキー
    """
    headers = {
        'Ocp-Apim-Subscription-Key': key
    }
    issue_token_url = 'https://api.cognitive.microsoft.com/sts/v1.0/issueToken'
    r = requests.post(issue_token_url, headers=headers)
    return r.text


# トークンを取得する
token = get_access_token(settings.TRANSLATOR_API_KEY)


@respond_to('^(translate|翻訳)(\s+-[-\w]+)?\s+(.*)')
def translate(message, cmd, option, text):
    """
    指定した文字列を翻訳する
    """
    if text in ('help', 'list'):
        return

    lang = 'ja'
    if option:
        # 指定した言語に翻訳する
        _, lang = option.split('-', 1)
    elif detect(text) in ('ja', 'ko'):
        # 漢字が多いと日本語なのに ko と判定される
        # 日本語の場合は英語に翻訳する
        lang = 'en'

    headers = {
        'Authorization': 'Bearer ' + token
    }
    query = {
        'to': lang,
        'text': text,
    }
    url = 'https://api.microsofttranslator.com/V2/Http.svc/Translate'
    r = requests.get(url, headers=headers, params=query)

    if r.status_code == 400:
        # エラーが発生したので内容を表示する
        error_message = r.text
        if "Message: 'to' must be a valid language" in error_message:
            message.send('`{}` は無効な言語です'.format(lang))
        else:
            message.send('エラーが発生しました\n```\n{}\n```'.format(r.text))
        return

    tree = ET.fromstring(r.text)
    message.send(tree.text)


@respond_to('^(translate|翻訳)\s+(list|リスト)')
def translate_list(message, cmd, option):
    """
    言語のリストを返す
    """
    #languages = translator.get_languages()
    #reply = ' '.join(['`{}`'.format(x) for x in languages])
    #message.send('使用できる言語: {}'.format(reply))
    pass


@respond_to('^(translate|翻訳)\s+help')
def translate_help(message, cmd):
    message.send('''`$translate python`, `$翻訳 python`: 指定した文字列を日本語に翻訳
`$translate へび`, `$翻訳 蛇`: 指定した文字列を英語に翻訳
`$translate -ru へび` `$翻訳 -ru へび`: 指定した言語(ru等)に翻訳
`$translate list` `$翻訳 リスト`: 使用できる言語の一覧を返す
''')

