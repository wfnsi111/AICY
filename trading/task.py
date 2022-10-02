import time
from celery import shared_task
from .strategy.main import start_my_strategy


@shared_task()
def start_my_strategy_by_celery(strategy_name, kwargs):
    start_my_strategy(strategy_name, kwargs)
    return 'OK'
