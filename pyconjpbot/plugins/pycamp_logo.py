import os
from io import StringIO

from PIL import Image, ImageFont, ImageDraw
from slackbot.bot import respond_to
from slackbot.utils import create_tmp_file
from ..botmessage import botsend, botwebapi

MAIN_COLOR = (90, 200, 233)
TEXT_SIZE = 120
TEXT_HEIGHT = 200
FONT = 'RictyDiminished-Regular.ttf'
IMAGES = (
        ('pycamp_logo.png', (1080, 1080)),
        ('pycamp_logo_horizontal.png', (2827, 1080)),
)

@respond_to('^pycamp\s+logo\s+(\S+)')
def pycamp_logo(message, title):
    botsend(message, 'Python Boot Camp ロゴ作成中... :hammer:')

    for name, size in IMAGES:
        logo_image = Image.open(os.path.join('templates', name))
        logo_image = logo_image.convert('RGBA')
        logo_image.thumbnail(size)

        width, height = size

        background = Image.new('RGBA', (width, TEXT_HEIGHT), MAIN_COLOR)
        font = ImageFont.truetype(os.path.join('fonts', FONT), size=TEXT_SIZE)
        draw = ImageDraw.Draw(background)
        text_width, _ = draw.textsize(title, font=font)
        draw.text(((width - text_width) / 2, 0), title, font=font, fill=(0, 0, 0))

        logo_image.paste(background, (0, height - TEXT_HEIGHT))

        with create_tmp_file() as tmpf:
            logo_image.save(tmpf, 'png')
            message.channel.upload_file(name, tmpf)

    botsend(message, '作成完了 :thumbsup:')
