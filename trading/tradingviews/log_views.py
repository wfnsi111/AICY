import os

from django.shortcuts import render
from trading.tradingviews.login_views import islogin


@islogin
def check_log(request):
    # 获取日志文件路径
    cur_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(cur_dir, 'strategy', 'log')
    try:
        logs = os.listdir(log_dir)
    except FileNotFoundError:
        logs = ["系统找不到指定的日志文件路径"]
    return render(request, 'trading/checklog.html', {'logs': logs})


@islogin
def show_log(request, log_id):
    cur_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(cur_dir, 'strategy', 'log', log_id)
    try:
        f = open(log_file, 'r', encoding='utf-8')
        file_content = f.read()
        f.close()
    except FileNotFoundError:
        return render(request, 'trading/checklog.html', {'logs': ''})
    return render(request, 'trading/showlog.html', {'file_content': file_content})
