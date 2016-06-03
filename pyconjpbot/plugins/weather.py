import os
import json

from slackbot.bot import respond_to
import requests
from bs4 import BeautifulSoup

WEATHER_URL = 'http://weather.livedoor.com/forecast/webservice/json/v1?city={}'
CODE_URL = 'http://weather.livedoor.com/forecast/rss/primary_area.xml'
        
WEATHER_EMOJI = {
    '晴れ': ':sunny:',
    '晴のち曇': ':mostly_sunny:',
    '曇時々晴': ':partly_sunny:',
    '雨時々曇': ':rain_cloud:',
    '曇のち雨': ':rain_cloud:',
    '曇時々雨': ':rain_cloud:',
    '雨': ':umbrella:',
    }

CITY_CODE_FILE = 'city_code.json'

def get_city_code():
    """
    cityコードの一覧を取得する
    """

    city_dict = {}

    # cityコードのjsonファイルが存在する場合はそこから読み込む
    if os.path.exists(CITY_CODE_FILE):
        with open(CITY_CODE_FILE) as f:
            city_dict = json.load(f)

    else:
        r = requests.get(CODE_URL)
        soup = BeautifulSoup(r.content, 'html.parser')

        for city in soup.findAll('city'):
            city_dict[city['title']] = city['id']

        with open(CITY_CODE_FILE, 'w') as f:
            json.dump(city_dict, f, indent=2, ensure_ascii=False)

    return city_dict

# cityコードの辞書を取得する
city_dict = get_city_code()

def _get_forecast_text(forecast):
    """
    天気予報の情報をテキストに変換する
    """
    date = forecast['dateLabel']
    telop = forecast['telop']
    temp = forecast['temperature']
    
    text = '{} は {}{}'.format(date, WEATHER_EMOJI.get(telop, ''), telop)
    if temp['min']:
        text += ' 最低気温{}℃'.format(temp['min']['celsius'])
    if temp['max']:
        text += ' 最高気温{}℃'.format(temp['max']['celsius'])

    return text

@respond_to('(weather|天気)$')
@respond_to('(weather|天気)\s+(.*)')
def weather(message, command, place='東京'):
    """
    天気予報を返す
    """
    if place in ('help', 'list'):
        return
    
    code = city_dict.get(place)

    if code is None:
        message.send('指定された地域は存在しません')
        return
        
    r = requests.get(WEATHER_URL.format(code))
    data = r.json()

    city = data['location']['city']
    #time = parser.parse(data['publicTime'])
    link = data['link']
    text = _get_forecast_text(data['forecasts'][0]) + '\n'
    text += _get_forecast_text(data['forecasts'][1])

    attachments = [{
        'fallback': '{}の天気予報'.format(city),
        'pretext': '<{}|{}の天気予報>'.format(link, city),
        'text': text,
    }]

    message.send_webapi('', json.dumps(attachments))

@respond_to('(weather|天気)\s+list')
def weather(message, command):
    reply = ' '.join(['`{}`'.format(x) for x in city_dict])
    message.send('指定可能な地域: {}'.format(reply))
    
@respond_to('(weather|天気)\s+help')
def weather(message, command):
    message.send('''`$weather` `$天気`: 東京の天気予報を返す
`$weather 釧路` `$天気 釧路`: 指定した地域の天気予報を返す
`$weather list` `$天気 list`: 指定可能な地域の一覧を返す
''')
