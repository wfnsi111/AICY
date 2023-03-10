import time
import platform
from .strategy.main import start_my_strategy

plat = platform.system().lower()
if plat != 'windows':
    from celery import shared_task

    @shared_task()
    def start_my_strategy_by_celery(strategy_name, kwargs):
        start_my_strategy(strategy_name, kwargs)
        return 'OK'
