from django.conf import settings
from django.urls import path, re_path
from django.contrib import admin
from django.views.static import serve

from . import views
from . import trading_views, account_views

app_name = 'trading'


urlpatterns = [
    path('index', views.index, name='index'),

    # 例如: /trading/1/
    path('<int:question_id>/', views.detail, name='detail'),

    # 例如: /trading/5/results/
    path('<int:question_id>/results/', views.results, name='results'),

    # 例如: /trading/5/vote/
    path('<int:question_id>/vote/', views.vote, name='vote'),

    path('admin/', admin.site.urls),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}, ),
    re_path(r'^trading/static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT},
            name='data-front/static'),

    path('', trading_views.trading_index, name='trading'),
    path('maalarm/', trading_views.maalarm, name='maalarm'),
    path('matrade/', trading_views.matrade, name='matrade'),
    path('trade/', trading_views.trade, name='trade'),
    path('stop_processing_account/', trading_views.stop_processing_account, name='stop_processing_account'),
    path('close_positions_all/', trading_views.close_positions_all, name='close_positions_all'),
    path('close_positions_one/', trading_views.close_positions_one, name='close_positions_one'),
    path('accountinfo/', trading_views.account_info, name='account_info'),
    path('addaccount/', account_views.addaccount, name='addaccount'),
    path('test/', trading_views.test, name='test'),
    path('test2/', views.test2, name='test2'),
    path('task_views/', views.task_views, name='task_views'),
    path('orderinfo/', trading_views.orderinfo_show, name='orderinfo'),
    path('strategy/', trading_views.strategyinfo, name='strategyinfo'),
    path('stop_processing_strategy/', trading_views.stop_processing_strategy, name='stop_processing_strategy'),

]
