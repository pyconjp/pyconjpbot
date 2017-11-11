from urllib.parse import urlparse
from io import BytesIO
from tempfile import NamedTemporaryFile

from slackbot.bot import respond_to
import requests
from PIL import Image, ImageDraw, ImageFont

from ..botmessage import botsend

HELP = """
`$lgtm create URL`: 指定したURLの画像をもとにLGTM画像を生成する
"""

font = ImageFont.truetype('Helvetica', 100, encoding="utf-8")


def generate_lgtm_image(im):
    """
    LGTM画像を生成して返す

    :params im: PillowのImageオブジェクト
    """
    draw_im = ImageDraw.Draw(im)
    width, height = im.size
    draw_im.text((width * 0.5 - 100, height * 0.7), "LGTM", font=font,
                 fill="#FFF")
    return im


@respond_to('^lgtm\s+create\s+(\S+)')
def lgtm_create(message, url):
    try:
        url = url.replace('<', '').replace('>', '')
        r = requests.get(url)
    except:
        botsend(message, '正しい画像URLを指定してください')
        return

    if r.status_code != requests.codes.ok:
        botsend(message, 'エラーが発生しました({})'.format(r.status_code))
        return

    try:
        # 画像を読み込む
        im = Image.open(BytesIO(r.content))
    except OSError:
        botsend(message, '画像ファイルのURLを指定してください')
        return

    # ファイルのbasenameを取得
    basename = urlparse(url).path.split('/')[-1].split('.')[0]

    # LGTM画像を生成する
    im = generate_lgtm_image(im)

    # 一時ファイルに画像を保存してアップロードする
    with NamedTemporaryFile(suffix='.png') as fp:
        im.save(fp, format='png')
        fname = '{}-lgtm.png'.format(basename)
        message.channel.upload_file(fname=fname, fpath=fp.name)


@respond_to('^lgtm\s+help')
def lgtm_help(message):
    """
    ヘルプメッセージを返す
    """
    botsend(message, HELP)
