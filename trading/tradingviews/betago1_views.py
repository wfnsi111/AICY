import json
import platform
import os

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from trading.models import AccountInfo, OrderInfo, Strategy, PlaceAlgo
from trading.strategy.okx.AccountAndTradeApi import AccountAndTradeApi
from trading.task import *
from trading.tradingviews.login_views import islogin


trading_status = {
    -2: "强制退出",
    -1: '出现错误',
    0: '空闲中',
    1:  '等待信号1',
    2:  '等待信号2',
    3:  '等待信号3',
    4:  '准备开仓',
    5:  '开仓成功',
    6:  '有账户异常',
    7:  '止盈',
    8:  '止损',
}


# gt 大于某个值
# gte 大于或等于某个值
# lt  小于某个值
# lte 小于或等于某个值

@islogin
def betago1(request):
    accountinfos = AccountInfo.objects.filter(is_active=1).filter(status__in=(-2, 0))
    return render(request, 'trading/betago1.html', {'accountinfos': accountinfos})


@islogin
def betago1_start_trade(request):
    if request.method == 'POST':
        instId = request.POST.get('instId', '')
        bar = request.POST.get('bar', '')
        if not bar or not instId:
            return HttpResponse('参数设置错误---[货币: %s]---[周期: %s]' % (instId, bar))
        all_accountinfo = request.POST.getlist('select2')
        if not all_accountinfo:
            return HttpResponse('未选择账户')

        strategy_name = 'BetaGo1'

        kw = {
            'instId': instId,
            "bar2": bar,
            "accountinfo": all_accountinfo,
            "trader": request.session.get('username'),
            "logfile": 'betago1',
        }

        try:
            plat = platform.system().lower()
            if plat == 'windows':
                start_my_strategy(strategy_name, kw)
            else:
                # celery 管理任务
                result = start_my_strategy_by_celery.delay(strategy_name, kw)
        except Exception as e:
            print(e)
        return HttpResponse('策略启动成功')
