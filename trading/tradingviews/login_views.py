from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from trading.models import NewUser, Trader


def islogin(func_name):
    # 登录装饰器
    def wrapper(request, *args, **kwargs):
        if request.session.get('username', ''):
            # 说明当前处于登录状态，直接调用func_name即可。
            if request.session.get('lever', '') == 1:
                return func_name(request, *args, **kwargs)
            else:
                # 此时需要获取用户所点击的url，并保存在cookie中，再跳转到登录页面。
                response = HttpResponseRedirect('/trading/login/')
                # 用户点击链接，会发送GET请求，对应的request对象中，含有要请求的url地址、请求参数、等等。
                response.set_cookie('click_url', request.path)
                return response
        else:
            # 此时需要获取用户所点击的url，并保存在cookie中，再跳转到登录页面。
            response = HttpResponseRedirect('/trading/login/')
            # 用户点击链接，会发送GET请求，对应的request对象中，含有要请求的url地址、请求参数、等等。
            response.set_cookie('click_url', request.path)
            return response
    return wrapper


def user_login(func_name):
    # 登录装饰器
    def wrapper(request, *args, **kwargs):
        if request.session.get('username', ''):
            # 说明当前处于登录状态，直接调用func_name即可。
            if request.session.get('lever', '') == 1:
                return func_name(request, *args, **kwargs)
            else:
                # 此时需要获取用户所点击的url，并保存在cookie中，再跳转到登录页面。
                response = HttpResponseRedirect('/trading/login/')
                # 用户点击链接，会发送GET请求，对应的request对象中，含有要请求的url地址、请求参数、等等。
                response.set_cookie('click_url', request.path)
                return response
        else:
            # 此时需要获取用户所点击的url，并保存在cookie中，再跳转到登录页面。
            response = HttpResponseRedirect('/trading/login/')
            # 用户点击链接，会发送GET请求，对应的request对象中，含有要请求的url地址、请求参数、等等。
            response.set_cookie('click_url', request.path)
            return response
    return wrapper


def tologin(request):
    if request.method == 'GET':
        return render(request, 'trading/login.html')
    elif request.method == 'POST':
        phonenumber = request.POST.get("phonenumber", '').strip()
        password = request.POST.get("password", '').strip()
        user = Trader.objects.filter(account=phonenumber).filter(password=password).first()
        if user:
            # 允许登录，保存登录的session信息。
            request.session['username'] = phonenumber
            request.session['lever'] = user.lever
            # 重定向：需要区分用户直接点击的登录页面进行的登录，还是由其他的页面跳转过来的。
            # 如果用户直接访问的是登录页面，那么直接跳转到首页。
            # 如果是从其它页面跳转过来的，需要获取用户所点击的url地址。比如：用户点击文章标题之后跳转的；用户点击评论之后跳转的；登录之后，直接重定向到用户点击的Url地址。
            user_click_url = request.COOKIES.get('click_url', '')
            if not user_click_url:
                # 说明是用户直接访问的就是登录页面
                return redirect(reverse('trading:trading'))
            else:
                # 说明是点击其他链接，跳转过来的。
                return redirect(user_click_url)
        else:
            error_msg = '用户名或密码错误'
            return render(request, 'trading/login.html', {'error_msg': error_msg})


def toregister(request):
    if request.method == 'GET':
        return render(request, 'trading/register.html')
    username = request.POST.get("username")
    phonenumber = request.POST.get("phonenumber")
    password = request.POST.get("password", '')
    password2 = request.POST.get("password2", '')
    invitation_code = request.POST.get("invitation_code", '')
    if len(phonenumber.strip()) != 11 or not phonenumber.isdigit():
        error_msg = '手机号错误'
        return render(request, 'trading/register.html', {"error_msg": error_msg})
    if password2.strip() != password.strip():
        error_msg = '两次密码不一致'
        return render(request, 'trading/register.html', {"error_msg": error_msg})
    # sendmsg = WeixinSMS()
    # code = sendmsg.send_msg_with_param()

    if Trader.objects.filter(account=phonenumber).exists():
        error_msg = '手机号已注册'
        return render(request, 'trading/register.html', {"error_msg": error_msg})

    user = Trader(name=username, account=phonenumber, password=password)
    user.save()
    return redirect(reverse('trading:tologin'))


def tologout(request):
    request.session.flush()
    return redirect(reverse('trading:trading_no_login'))


def logout(request):
    request.session.flush()
    return redirect(reverse('user_web:index'))
