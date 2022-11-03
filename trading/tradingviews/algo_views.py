from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from trading.models import AccountInfo, Strategy, PlaceAlgo
from trading.strategy.okx.AccountAndTradeApi import AccountAndTradeApi
from trading.tradingviews.login_views import islogin

"""
status = -2  # 手动设置止损止盈出现错误
status = 0  # 无效订单
status = 1  # 策略设置止损止盈
status = 2  # 已取消策略设置的止损止盈
status = 3  # 手动设置止损止盈
"""


@islogin
def reset_place_algo(request):
    if request.method == 'POST':
        tptriggerpx = request.POST.get('algo_tp')
        sltriggerpx = request.POST.get('algo_sl')
        strategy_id = request.POST.get('algo_number')
        trade_code = request.POST.get('trade_code')
        if not all([tptriggerpx, sltriggerpx, strategy_id]):
            return HttpResponse('委托单设置错误')

        if trade_code.strip().lower() != 'lgh':
            return HttpResponse('密码错误')

        try:
            strategyinfo = Strategy.objects.get(pk=int(strategy_id))
            all_algo_orders = PlaceAlgo.objects.filter(strategyid=strategyinfo.id).filter(status__gte=1)
        except Exception as e:
            print(e)
            return HttpResponse('委托单设置错误')

        if not all_algo_orders:
            return HttpResponse('未查询到之前的委托信息')

        # 错误标识 有一个账户发生错误则为Ture
        error_code = False

        # -1 为市价平仓
        tpordpx = "-1"
        slordpx = "-1"

        for order in all_algo_orders:
            accountinfo = AccountInfo.objects.get(pk=order.accountinfo_id)
            obj_api = AccountAndTradeApi(accountinfo.api_key, accountinfo.secret_key, accountinfo.passphrase, False,
                                         accountinfo.flag)
            algoid = order.algoid
            instid = order.instid

            if order.status != 2:
                try:
                    cancel_result, msg = obj_api.cancel_place_algo_order(algoid, instid)
                except Exception as e:
                    error_code = True
                    cancel_result = False
                    print(e)
            else:
                cancel_result = True

            # 成功取消委托订单
            if cancel_result:
                order.status = 2
                order.save()

                side = 'sell' if order.posside == 'long' else 'buy'
                try:
                    result = obj_api.tradeAPI.place_algo_order(instid, 'cross', side, ordType='oco', sz=order.sz,
                                                               posSide=order.posside, tpTriggerPx=tptriggerpx,
                                                               tpOrdPx=tpordpx, slTriggerPx=sltriggerpx, slOrdPx=slordpx,
                                                               tpTriggerPxType='last', slTriggerPxType='last')
                    for data in result.get('data'):
                        scode = data.get('sCode')
                        if scode == "0":
                            print('止损止盈重设成功')
                            order.status = 0
                            order.save()

                            # order.pk = None 重新复制一条订单记录
                            order.pk = None
                            order.algoid = data.get("algoId")
                            order.tptriggerpx = tptriggerpx
                            order.tpordpx = tpordpx
                            order.sltriggerpx = sltriggerpx
                            order.slordpx = slordpx
                            order.status = 3
                            order.save()

                        else:
                            # 止损止盈的价格设置不合理，需要重新设置
                            print('止损止盈重设出现错误！！！！！！！！！！！！！！')
                            order.scode = scode
                            order.smsg = data.get("sMsg")
                            order.save()
                            if scode in ('51277', '51278', '51279', '51280'):
                                return HttpResponse(data.get("sMsg"))

                except Exception as e:
                    error_code = True
                    print(e)

            else:
                print(accountinfo.account_text)
                print('取消策略的委托单出现错误!!!')

        if error_code:
            return HttpResponse("某些账户出现未知错误， 请再出确认！！！")

        return redirect(reverse('trading:account_info'))





