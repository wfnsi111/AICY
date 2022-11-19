from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .task import *
from .models import Question, Choice


def index(request):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    context = {
        'latest_question_list': latest_question_list,
    }
    return render(request, 'trading/index.html', context)



def add_smoke(request):
    '''
        新增冒烟测试记录
        :param request:
        :return:
        '''

    if request.method == "POST":
        project_name = request.POST.get("project_name", None)
        version = request.POST.get("version", None)
        submit_test_time = request.POST.get("submit_test_time", None)
        case_num = request.POST.get("case_num", None)
        executed_num=request.POST.get("executed_num", None)
        pass_num=request.POST.get("pass_num", None)
        fail_num=request.POST.get("fail_num", None)

    return HttpResponse('statussuccess')


def boot2(request):
    return render(request, 'trading/boot2.html')


def boot3(request):
    return render(request, 'trading/boot3.html')