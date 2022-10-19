from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from trading.models import AccountInfo, AccountAssetBills
from trading.strategy.okx.AccountAndTradeApi import AccountAndTradeApi
from trading.tradingviews.login_views import islogin
from trading.strategy.conf.account_bills_type import account_bills_type

import time


@islogin
def addaccount(request):
    if request.method == "GET":
        return render(request, 'trading/addaccount.html')
    one_accountinfo = AccountInfo()
    one_accountinfo.trader_id = 1
    one_accountinfo.account_text = request.POST.get('account_text')
    one_accountinfo.secret_key = request.POST.get('secret_key')
    one_accountinfo.api_key = request.POST.get('api_key')
    one_accountinfo.passphrase = request.POST.get('passphrase')
    one_accountinfo.phone = request.POST.get('phone', '')
    one_accountinfo.email = request.POST.get('email', '')
    one_accountinfo.balance = request.POST.get('balance', '')
    one_accountinfo.promoter = request.POST.get('promoter', '')
    one_accountinfo.save()

    return render(request, 'trading/accountshow.html', {"accountinfo": one_accountinfo})


@islogin
def del_account(request):
    pass


@islogin
def check_account_funding(request):
    account_all = AccountInfo.objects.filter(is_active=0).filter(flag=0)
    for account_obj in account_all:
        show_data = {}
        try:
            api_obj = AccountAndTradeApi(account_obj.api_key, account_obj.secret_key, account_obj.passphrase,
                                         False, account_obj.flag)
            # api_obj.check_account_funding_()
            api_obj.get_asset_bills()
        except Exception as e:
            print(e)


@islogin
def get_account_asset_bills(request):
    """ 获取账户的资金流水 """
    account_all = AccountInfo.objects.filter(is_active=1).filter(flag=0)
    bills_list_to_insert = []
    for account_obj in account_all:
        account_id = account_obj.id
        try:
            api_obj = AccountAndTradeApi(account_obj.api_key, account_obj.secret_key, account_obj.passphrase,
                                         False, account_obj.flag)
            result = api_obj.get_asset_bills()
            if not result:
                print('no data')
            else:
                for data in result:
                    billid = data.get("billId")
                    if AccountAssetBills.objects.filter(billid=billid).exists():
                        continue
                    one_bill = AccountAssetBills()
                    one_bill.accountinfo_id = account_id
                    one_bill.bal = data.get("bal")
                    one_bill.balchg = data.get("balChg")
                    one_bill.billid = data.get("billId")
                    one_bill.ccy = data.get("ccy")
                    one_bill.type = account_bills_type.get(data.get("type"))
                    bills_list_to_insert.append(one_bill)
                    ts = timestamp_to_date(data.get("ts"))
                    one_bill.bill_date = ts

        except Exception as e:
            print(e)
    if bills_list_to_insert:
        try:
            AccountAssetBills.objects.bulk_create(bills_list_to_insert)
        except Exception as e:
            print(e)
    return HttpResponse('OK')


def timestamp_to_date(t):
    # 13位时间戳转日期
    timestamp = float(t)/1000
    timearray = time.localtime(timestamp)
    date = time.strftime("%Y-%m-%d %H:%M:%S", timearray)
    return date


@islogin
def check_account_asset_bills(request):
    # get_account_asset_bills(request)
    if request.method == 'GET':
        all_accountinfo = AccountInfo.objects.filter(is_active=1).filter(flag=0)
        return render(request, 'trading/bills.html', {'all_accountinfo': all_accountinfo})

    if request.method == 'POST':
        accountinfo_id = request.POST.get('accountinfo_id', '')
        acc = AccountInfo.objects.get(pk=accountinfo_id)
        bills = acc.accountassetbills_set.all().order_by('-bill_date')
        # bills = AccountAssetBills.objects.filter(accountinfo_id=int(accountinfo_id))
        return render(request, 'trading/bills1.html', {"bills": bills})