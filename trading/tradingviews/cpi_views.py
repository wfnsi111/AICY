import requests

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from trading.models import AccountInfo, Strategy, PlaceAlgo
from trading.strategy.okx.AccountAndTradeApi import AccountAndTradeApi
from trading.tradingviews.login_views import islogin
from ..strategy.main import start_my_strategy



# def get_jin10_data(request):
#     url = 'https://rili.jin10.com/'
#     User_Agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
#
#     response = requests.get(url, headers={'User-Agent': User_Agent})    #把头部增加到请求中去
#     html = response.text


@islogin
def hedging(request):
    accountinfos = AccountInfo.objects.filter(is_active=2)
    if request.method == 'GET':
        return render(request, 'trading/HedgeTransaction.html', {'accountinfos': accountinfos})
    trade_code = request.POST.get('trade_code', '')
    if not trade_code.strip().lower() == '520520':
        return HttpResponse('验证码错误')

    sz = request.POST.get('sz', '')
    instId = request.POST.get('instId', '')
    lever = request.POST.get('lever', '')
    mgnMode = request.POST.get('mgnMode', '')
    algo_tp = request.POST.get('algo_tp', '')
    algo_sl = request.POST.get('algo_sl', '')
    first = request.POST.get('first', '')

    all_accountinfo = request.POST.getlist('select2')
    if not all_accountinfo:
        return HttpResponse('未选择账户')
    strategy_name = 'HedgeTransaction'

    kw = {
        'instId': instId,
        "sz": sz,
        "lever": lever,
        "mgnMode": mgnMode,
        "accountinfo": all_accountinfo,
        "trader": request.session.get('username'),
        "logfile": 'hedging',
        "algo_tp": algo_tp,
        "algo_sl": algo_sl,
        "first": first,
    }

    try:
        pass
        start_my_strategy(strategy_name, kw)
    except Exception as e:
        print(e)
    return HttpResponse('策略启动成功')

