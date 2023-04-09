
from django.http import HttpResponse
from .models import Question, OrderInfo, AccountInfo
from trading.strategy.okx.AccountAndTradeApi import AccountAndTradeApi

import copy
def index(request):
    """
    sell: open - close ) * sz * 0.1 = pnl
    buy:  close -open ) * sz * 0.1 = pnl
    :param request:
    :return:


    """
    account_id = 10

    # orgaccount = AccountInfo.objects.filter(id=42).first()
    # write_account = AccountInfo.objects.filter(id=2).first()

    # org_api = AccountAndTradeApi(orgaccount.api_key, orgaccount.secret_key, orgaccount.passphrase, False,orgaccount.flag)
    # write_account = AccountAndTradeApi(orgaccount.api_key, orgaccount.secret_key, orgaccount.passphrase, False,orgaccount.flag)
    result = OrderInfo.objects.filter(accountinfo=16).filter(id__lte=358).all()
    # result = OrderInfo.objects.filter(accountinfo=42).all()
    count = 1
    pret = 1.4    # 系数
    # pnl_price = - 80
    pnl_price = - 21.748
    for orderinfo in result:
        if not orderinfo.pnl:
            print(count)
            count += 1
            continue
        new_orderinfo = copy.deepcopy(orderinfo)
        new_orderinfo.id = orderinfo.id * 10000 + orderinfo.id
        new_orderinfo.sz = int(int(orderinfo.sz) * pret)

        if orderinfo.posside == 'long':
            new_orderinfo.pnl = (float(orderinfo.closeavgpx) - float(orderinfo.avgpx)) * float(new_orderinfo.sz) * 0.1
            if float(orderinfo.pnl) <= pnl_price:
            # if float(orderinfo.pnl) <= - 80:
                new_orderinfo.posside = 'short'
                new_orderinfo.side = 'sell'
                new_orderinfo.pnl = abs(new_orderinfo.pnl)
        else:
            new_orderinfo.pnl = (float(orderinfo.avgpx) - float(orderinfo.closeavgpx)) * float(new_orderinfo.sz) * 0.1
            if float(orderinfo.pnl) <= pnl_price:
                new_orderinfo.posside = 'short'
                new_orderinfo.side = 'sell'
                new_orderinfo.pnl = abs(new_orderinfo.pnl)


        new_orderinfo.pnl = "%.2f" % new_orderinfo.pnl
        # 要改的账户
        new_orderinfo.accountinfo_id = 2
        # new_orderinfo.create_time = orderinfo.create_time
        # new_orderinfo.update_time = orderinfo.update_time

        new_orderinfo.save()
    orderinfo2 = OrderInfo(id=999999999, ordid="999999999", instid='', close_position=1, status=1, accountinfo_id=2)
    orderinfo2.save()
    return HttpResponse('OK')


def copy_data(request):
    start_id = 10000
    account1_id = 10
    account2_id = 2
    pret = 0.8  # 系数
    OrderInfo.objects.filter(accountinfo=account2_id).delete()
    result = OrderInfo.objects.filter(accountinfo=account1_id).all()
    for orderinfo in result:
        new_orderinfo = copy.deepcopy(orderinfo)
        new_orderinfo.sz = int(int(orderinfo.sz) * pret)
        try:
            new_orderinfo.pnl = "%.2f" % (float(orderinfo.pnl) * pret)
        except Exception as e:
            print(e)
        new_orderinfo.accountinfo_id = account2_id
        new_orderinfo.id = account2_id * 100000+orderinfo.id
        new_orderinfo.save()

    return HttpResponse('OK')


def get_order_history(request):
    acc = AccountInfo.objects.get(id=42)
    obj_api = AccountAndTradeApi(acc.api_key, acc.secret_key, acc.passphrase, False, acc.flag)
    result = obj_api.tradeAPI.get_orders_history('SWAP', limit=25)
    data = result.get("data")
    for item in data:
        print("avgPx:", item['avgPx'],"pnl:", item['pnl'],"sz:", item['sz'],"posSide:", item['posSide'],"side:", item['side'],"ordId:", item['ordId'],)
    return HttpResponse('OK')