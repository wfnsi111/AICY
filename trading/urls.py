from django.urls import path

from . import views
from .tradingviews import login_views, trading_views, account_views, algo_views, log_views, cpi_views

app_name = 'trading'


urlpatterns = [
    path('index', views.index, name='index'),
    path('login/', login_views.tologin, name='tologin'),
    path('logout/', login_views.tologout, name='tologout'),

    # views
    path('boot2/', views.boot2, name='boot2'),
    path('boot3/', views.boot3, name='boot3'),

    # trading_views
    path('', trading_views.trading_index, name='trading'),
    path('betago/', trading_views.trading_index_no_login, name='trading_no_login'),     # 不需要登录
    path('maalarm/', trading_views.maalarm, name='maalarm'),
    path('matrade/', trading_views.matrade, name='matrade'),
    path('matrade_open_order/', trading_views.matrade_open_order, name='matrade_open_order'),
    path('trade/', trading_views.trade, name='trade'),
    path('stop_processing_account/', trading_views.stop_processing_account, name='stop_processing_account'),
    path('close_positions_all/', trading_views.close_positions_all, name='close_positions_all'),
    path('close_positions_one/', trading_views.close_positions_one, name='close_positions_one'),
    path('orderinfo/', trading_views.orderinfo_show, name='orderinfo'),
    path('orderinfo2/', trading_views.orderinfo_show_no_login, name='orderinfo_no_login'),
    path('strategy/', trading_views.strategyinfo, name='strategyinfo'),
    path('strategy2/', trading_views.strategyinfo_no_login, name='strategyinfo_no_login'),
    path('stop_processing_strategy/', trading_views.stop_processing_strategy, name='stop_processing_strategy'),

    # log_views
    path('log/', log_views.check_log, name='check_log'),
    path('showlog/<log_id>', log_views.show_log, name='show_log'),

    # account_views
    path('accountinfo/', account_views.account_info, name='account_info'),
    path('accountinfo2/', account_views.account_info_no_login, name='account_info_no_login'),
    path('addaccount/', account_views.addaccount, name='addaccount'),
    path('bills/', account_views.check_account_asset_bills, name='check_account_asset_bills'),
    path('up_bills/', account_views.get_account_asset_bills, name='get_account_asset_bills'),

    # algo_views
    path('algo/', algo_views.reset_place_algo, name='reset_place_algo'),

    # cpi_views
    path('cpi/', cpi_views.get_jin10_data, name='get_jin10_data'),

]
