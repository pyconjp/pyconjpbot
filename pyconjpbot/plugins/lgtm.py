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

# 文字の色と影の色
FILL = 'white'
SHADOW = 'black'


def get_font_size(size, font_name, text):
    """
    指定したテキストを画像に配置する時にいい感じのフォントサイズを返す

    :params size: 画像の幅と高さの短い方
    :params font_name: フォントの名前(Arial, Helvetica等)
    :params text: 描画する文字列(LGTM等)
    :return: フォントサイズ
    """
    # フォントのサイズを5ポイント刻みで大きくする
    for font_size in range(10, 200, 5):
        font = ImageFont.truetype(font_name, font_size, encoding="utf-8")
        # テキストの描画サイズを取得
        width, height = font.getsize(text)
        # テキストの幅が、画像の短い方の半分のサイズを越えたら終了
        if width > size / 2:
            break
    return font_size


def get_text_xy(width, height, font, text):
    """
    指定したテキストを配置する位置を位置を返す

    :params widht: 画像の幅
    :params height: 画像の高さ
    :params font: フォントオブジェクト
    :params text: 描画する文字列(LGTM等)
    :return: X座標, Y座標
    """
    # テキストの幅と高さを取得
    text_width, text_height = font.getsize(text)
    # テキストの配置する位置を計算
    x_center = width / 2 - text_width / 2
    # x_left = width / 20
    # x_right = width - width / 20 - text_width
    y_center = height / 2 - text_height / 2
    # y_top = height / 20
    # y_bottom = height - height / 20 - text_height
    return x_center, y_center


def generate_lgtm_image(im):
    """
    LGTM画像を生成して返す

    :params im: PillowのImageオブジェクト
    :return: LGTM画像のImageオブジェクト
    """
    # 画像が大きかったらリサイズする
    im.thumbnail((400, 400))
    width, height = im.size

    # フォント生成
    # Arial, Arial Black, Comic Sans MS, Courier New, Georgia, Impact
    # Times New Roman, Trebuchet MS, Verdana
    text = 'LGTM'
    font_name = 'Arial Black'
    font_size = get_font_size(min(width, height), font_name, text)
    font = ImageFont.truetype(font_name, font_size, encoding="utf-8")

    # テキストの描画位置の計算
    x, y = get_text_xy(width, height, font, text)

    draw_im = ImageDraw.Draw(im)
    # 枠線を描画
    draw_im.text((x-1, y-1), text, font=font, fill=SHADOW)
    draw_im.text((x+1, y-1), text, font=font, fill=SHADOW)
    draw_im.text((x-1, y+1), text, font=font, fill=SHADOW)
    draw_im.text((x+1, y+1), text, font=font, fill=SHADOW)
    # テキストを描画
    draw_im.text((x, y), text, font=font, fill=FILL)

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
