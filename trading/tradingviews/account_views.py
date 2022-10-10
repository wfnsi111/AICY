from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from trading.models import AccountInfo


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


def del_account(request):
    pass