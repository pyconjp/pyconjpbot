from slackbot.bot import respond_to, listen_to
from sympy import sympify, SympifyError

@listen_to('^(([-+*/^%()\d\s]|pi|e|sqrt|sin|cos|tan)+)$')
def calc(message, expression, dummy_):
    """
    数式っぽい文字列だったら計算して結果を返す
    """
    try:
        result = sympify(expression)
    except SympifyError:
        # 数式じゃなかったら無視する
        return
    
    if result.is_Integer:
        message.send(str(result))
    else:
        message.send(str(float(result.evalf())))


