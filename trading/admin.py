from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Trader, AccountInfo, Strategy, OrderInfo


admin.site.site_header = '交易员管理'
admin.site.site_title = '交易员管理'
admin.site.index_title = '交易员管理'


admin.site.register(Trader)
admin.site.register(AccountInfo)
admin.site.register(Strategy)
admin.site.register(OrderInfo)

