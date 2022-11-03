from django.urls import path

from . import views
from .tradingviews import login_views, trading_views, account_views, algo_views, log_views

app_name = 'trading'


urlpatterns = [
    path('index', views.index, name='index'),
    path('login/', login_views.tologin, name='tologin'),
    path('logout/', login_views.tologout, name='tologout'),

    # views
    path('boot2/', views.boot2, name='boot2'),

    # trading_views
    path('', trading_views.trading_index, name='trading'),
    path('maalarm/', trading_views.maalarm, name='maalarm'),
    path('matrade/', trading_views.matrade, name='matrade'),
    path('matrade_open_order/', trading_views.matrade_open_order, name='matrade_open_order'),
    path('trade/', trading_views.trade, name='trade'),
    path('stop_processing_account/', trading_views.stop_processing_account, name='stop_processing_account'),
    path('close_positions_all/', trading_views.close_positions_all, name='close_positions_all'),
    path('close_positions_one/', trading_views.close_positions_one, name='close_positions_one'),
    path('orderinfo/', trading_views.orderinfo_show, name='orderinfo'),
    path('strategy/', trading_views.strategyinfo, name='strategyinfo'),
    path('stop_processing_strategy/', trading_views.stop_processing_strategy, name='stop_processing_strategy'),

    # log_views
    path('log/', log_views.check_log, name='check_log'),
    path('showlog/<log_id>', log_views.show_log, name='show_log'),

    # account_views
    path('accountinfo/', account_views.account_info, name='account_info'),
    path('addaccount/', account_views.addaccount, name='addaccount'),
    path('funding/', account_views.check_account_funding, name='check_account_funding'),
    path('bills/', account_views.check_account_asset_bills, name='check_account_asset_bills'),
    path('up_bills/', account_views.get_account_asset_bills, name='get_account_asset_bills'),

    # algo_views
    path('algo/', algo_views.reset_place_algo, name='reset_place_algo'),

]
