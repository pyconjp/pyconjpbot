import json

from slackbot.bot import respond_to
import requests
from dateutil import parser

URL = 'http://weather.livedoor.com/forecast/webservice/json/v1?city={}'

WEATHER_EMOJI = {
    '晴れ': ':sunny:',
    '雨': ':umbrella:',
    }

def _get_forecast_text(forecast):
    """
    天気予報の情報をテキストに変換する
    """
    date = forecast['dateLabel']
    telop = forecast['telop']
    temp = forecast['temperature']
    
    text = '{}{}'.format(WEATHER_EMOJI.get(telop, ''), telop)
    if temp['min']:
        text += ' 最低気温{}℃'.format(temp['min']['celsius'])
    if temp['max']:
        text += ' 最高気温{}℃'.format(temp['max']['celsius'])

    return text

@respond_to('(weather|天気)')
def weather(message, command):
    """
    天気予報を返す
    """
    r = requests.get(URL.format('130010'))
    data = r.json()

    city = data['location']['city']
    time = parser.parse(data['publicTime'])
    link = data['link']
    text = _get_forecasst_text(data['forecasts'][0])

    attachments = [{
        'fallback': '{}の{}の天気'.format(city, date),
        'pretext': '<{}|{}の{}の天気> ({:%m月%d日%H:%M}発表)'.format(link, city, date, time),
        'text': text,
    }]

    message.send_webapi('', json.dumps(attachments))


    
    

