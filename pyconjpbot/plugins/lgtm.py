from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import requests
from PIL import Image, ImageDraw, ImageFont
from slackbot.bot import respond_to
from slackbot.dispatcher import Message

from ..botmessage import botsend

FONT = "NotoSansCJKjp-Bold.otf"

HELP = """
`$lgtm create URL (テキスト)`: 指定したURLの画像をもとにLGTM画像を生成する。テキストを指定するとそのテキストを描画する
"""

# 文字の色と影の色
FILL = "white"
SHADOW = "black"


def get_font_size(size: int, font_file: str, text: str) -> ImageFont:
    """
    指定したテキストを画像に配置する時にいい感じのフォントサイズを返す

    :params size: 画像の幅と高さの短い方
    :params font_file: フォントファイルのフルパス
    :params text: 描画する文字列(LGTM等)
    :return: フォントサイズ
    """
    # フォントのサイズを5ポイント刻みで大きくする
    for font_size in range(10, 200, 5):
        font = ImageFont.truetype(font_file, font_size, encoding="utf-8")
        # テキストの描画サイズを取得
        width, height = font.getsize(text)
        # テキストの幅が、画像の短い方の半分のサイズを越えたら終了
        if width > size / 2:
            break
    return font_size


def get_text_xy(
    width: int, height: int, font: ImageFont, text: str
) -> tuple[int, int, int, int]:
    """
    指定したテキストを配置する位置を返す

    :params widht: 画像の幅
    :params height: 画像の高さ
    :params font: フォントオブジェクト
    :params text: 描画する文字列(LGTM等)
    :return: X座標、Y座標(中央)、Y座標(上)、Y座標(下)
    """
    # テキストの幅と高さを取得
    text_width, text_height = font.getsize(text)
    # テキストの配置する位置を計算
    x_center = width / 2 - text_width / 2
    y_center = height / 2 - text_height / 2
    y_top = height / 5 - text_height / 2
    y_bottom = height / 5 * 4 - text_height
    return x_center, y_center, y_top, y_bottom


def generate_lgtm_image(im: Image, text: str) -> list[Image]:
    """
    LGTM画像を生成して返す

    :params im: PillowのImageオブジェクト
    :return: LGTM画像のImageオブジェクトのリスト
    """
    # 画像が大きかったらリサイズする
    im.thumbnail((400, 400))
    width, height = im.size

    # フォント生成
    font_file = str(Path(__file__).parent / "fonts" / FONT)
    font_size = get_font_size(min(width, height), font_file, text)
    font = ImageFont.truetype(font_file, font_size, encoding="utf-8")

    # テキストの描画位置の計算
    x, y_center, y_top, y_bottom = get_text_xy(width, height, font, text)

    images = []
    # 中央、上、下にテキストを描画する
    for y in y_center, y_top, y_bottom:
        copied_im = im.copy()
        images.append(copied_im)
        draw_im = ImageDraw.Draw(copied_im)
        # 枠線を描画
        draw_im.text((x - 1, y - 1), text, font=font, fill=SHADOW)
        draw_im.text((x + 1, y - 1), text, font=font, fill=SHADOW)
        draw_im.text((x - 1, y + 1), text, font=font, fill=SHADOW)
        draw_im.text((x + 1, y + 1), text, font=font, fill=SHADOW)
        # テキストを描画
        draw_im.text((x, y), text, font=font, fill=FILL)

    return images


@respond_to(r"^lgtm\s+create\s+(\S+)$")
@respond_to(r"^lgtm\s+create\s+(\S+)\s+(.+)")
def lgtm_create(message: Message, url: str, text: str = "LGTM") -> None:
    try:
        url = url.replace("<", "").replace(">", "")
        r = requests.get(url)
    except Exception:
        botsend(message, "正しい画像URLを指定してください")
        return

    if r.status_code != requests.codes.ok:
        botsend(message, f"エラーが発生しました({r.status_code})")
        return

    try:
        # 画像を読み込む
        im = Image.open(BytesIO(r.content))
    except OSError:
        botsend(message, "画像ファイルのURLを指定してください")
        return

    # ファイルのbasenameを取得
    basename = urlparse(url).path.split("/")[-1].split(".")[0]

    # LGTM画像を生成する
    images = generate_lgtm_image(im, text)

    for idx, im in enumerate(images):
        # 一時ファイルに画像を保存してアップロードする
        with NamedTemporaryFile(suffix=".png") as fp:
            im.save(fp, format="png")
            fname = f"{basename}-{text.lower()}{idx}.png"
            message.channel.upload_file(fname=fname, fpath=fp.name)


@respond_to(r"^lgtm\s+help")
def lgtm_help(message: Message):
    """
    ヘルプメッセージを返す
    """
    botsend(message, HELP)
