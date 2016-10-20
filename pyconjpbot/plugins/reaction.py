import re

from slackbot.bot import listen_to
from slacker import Error

# リアクション対象のキーワードと絵文字
REACTION = {
    ('肉', 'meat'): 'meat_on_bone',
    'カレーメシ': ('curry', 'boom'),
    ('ピザ', 'pizza'): 'pizza',
    ('sushi', '寿司', 'おすし'): 'sushi',
    '酒': 'sake',
    ('ビール', 'beer'): 'beer',
    'さくさく': 'panda_face',
    'お茶': 'tea',
    ('コーヒー', 'coffee'): 'coffee',
    'ケーキ': 'cake',
    ('ラーメン', 'ramen'): 'ramen',
}

def _react(message, emojis):
    """
    指定された emoji を reaction で返す
    """
    if isinstance(emojis, str):
        # tuple に変換する
        emojis = (emojis, )
    for emoji in emojis:
        try:
            message.react(emoji)
        except Error as error:
            # 同じリアクションをすると例外が発生するので、無視する
            if error.args[0] == 'already_reacted':
                pass
            else:
                raise

@listen_to('.')
def reaction(message):
    """
    メッセージの中にリアクションする文字列があれば、emojiでリアクションする
    """
    # テキスト全体をとりだす
    text = message.body['text'].lower()
    for words, emojis in REACTION.items():
        if isinstance(words, str):
            if words in text:
                _react(message, emojis)
        else:
            # 正規表現で指定した単語が存在するかチェックする
            if re.search('|'.join(words), text):
                _react(message, emojis)
