import json


from slackbot.bot import respond_to
import requests
from bs4 import BeautifulSoup

URL = 'http://weather.livedoor.com/forecast/webservice/json/v1?city={}'

WEATHER_EMOJI = {
    '晴れ': ':sunny:',
    '雨': ':umbrella:',
    }

def get_city_code():
    """
    cityコードの一覧を取得する
    """
    r = requests.get('http://weather.livedoor.com/forecast/rss/primary_area.xml')
    soup = BeautifulSoup(r.content, 'html.parser')

    city_dict = {}
    for city in soup.findAll('city'):
        city_dict[city['title']] = city['id']
    return city_dict

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
    code = city_dict.get(place)

    if code is None:
        message.send('指定された地域は存在しません')
        return
        
    r = requests.get(URL.format(code))
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

