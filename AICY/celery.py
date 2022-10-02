import os
from celery import Celery
from django.conf import settings
import django

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AICY.settings')
# django.setup()


# 实例化
celery_app = Celery('AICY')

# namespace='CELERY'作用是允许你在Django配置文件中对Celery进行配置
# 但所有Celery配置项必须以CELERY开头，防止冲突
celery_app.config_from_object('django.conf:settings')

# 自动从Django的已注册app目录下加载task.py
celery_app.autodiscover_tasks(settings.INSTALLED_APPS)


# 一个测试任务
@celery_app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')