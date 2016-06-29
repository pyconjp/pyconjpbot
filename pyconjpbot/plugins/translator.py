from slackbot import settings
from slackbot.bot import respond_to, listen_to

from microsofttranslator import Translator, ArgumentOutOfRangeException
from langdetect import detect

# Connect to Microsoft Translator
translator = Translator(settings.TRANSLATOR_ID, settings.TRANSLATOR_SECRET)

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
    try:
        message.send(translator.translate(text, lang))
    except ArgumentOutOfRangeException:
        message.send('`{}` は無効な言語です'.format(lang))

@respond_to('^(translate|翻訳)\s+(list|リスト)')
def translate_list(message, cmd, option):
    """
    言語のリストを返す
    """
    languages = translator.get_languages()
    reply = ' '.join(['`{}`'.format(x) for x in languages])
    message.send('使用できる言語: {}'.format(reply))
    
@respond_to('^(translate|翻訳)\s+help')
def translate_help(message, cmd):
    message.send('''`$translate python`, `$翻訳 python`: 指定した文字列を日本語に翻訳
`$translate へび`, `$翻訳 蛇`: 指定した文字列を英語に翻訳
`$translate -ru へび` `$翻訳 -ru へび`: 指定した言語(ru等)に翻訳
`$translate list` `$翻訳 リスト`: 使用できる言語の一覧を返す
''')

