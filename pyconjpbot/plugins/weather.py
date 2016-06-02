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
    
    text = '{} は {}{}'.format(date, WEATHER_EMOJI.get(telop, ''), telop)
    if temp['min']:
        text += ' 最低気温{}℃'.format(temp['min']['celsius'])
    if temp['max']:
        text += ' 最高気温{}℃'.format(temp['max']['celsius'])

    return text

@respond_to('(weather|天気予報)')
@respond_to('(weather|天気予報)\s+(.*)')
def weather(message, command, place='東京'):
    """
    天気予報を返す
    """
    r = requests.get(URL.format('130010'))
    data = r.json()

    city = data['location']['city']
    #time = parser.parse(data['publicTime'])
    link = data['link']
    text = _get_forecast_text(data['forecasts'][0]) + '\n'
    text += _get_forecast_text(data['forecasts'][1])

    attachments = [{
        'fallback': '{}の天気'.format(city),
        'pretext': '<{}|{}の天気>'.format(link, city),
        'text': text,
    }]

    message.send_webapi('', json.dumps(attachments))


    
    

