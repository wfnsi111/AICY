from django.urls import path

from . import views
from . import trading_views

app_name = 'trading'


urlpatterns = [
    path('index', views.index, name='index'),

    # 例如: /trading/1/
    path('<int:question_id>/', views.detail, name='detail'),

    # 例如: /trading/5/results/
    path('<int:question_id>/results/', views.results, name='results'),

    # 例如: /trading/5/vote/
    path('<int:question_id>/vote/', views.vote, name='vote'),


    path('', trading_views.trading_index, name='trading'),
    path('maalarm/', trading_views.maalarm, name='maalarm'),
    path('matrade/', trading_views.matrade, name='matrade'),
    path('login/', trading_views.login, name='login'),
    path('strategy/', trading_views.stop_processing_strategy, name='stop_processing_strategy'),
    path('close/', trading_views.close_positions_all, name='close_positions_all'),


]
