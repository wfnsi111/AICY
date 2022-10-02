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


# 注意函数的参数
def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'trading/detail.html', {'question': question})


def results(request, question_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % question_id)


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'trading/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
    return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


def test2(request):
    return render(request, 'trading/test2.html')


def task_views(request):
    result = add.delay(100, 200)
    print(result)
    return HttpResponse('调用函数结果')


from celery import result
def task_views2(request):
    task_id = request.GET.get('task_id')
    ar = result.AsyncResult(task_id)
    if ar.ready():
        print(ar.status)
        return HttpResponse(ar.get())
    else:
        print(ar.status)
        return HttpResponse(ar.status)
