from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import *

admin.site.site_header = '交易员管理'
admin.site.site_title = '交易员管理'
admin.site.index_title = '交易员管理'


# admin.site.register(Trader)
# admin.site.register(AccountInfo)
# admin.site.register(Strategy)
# admin.site.register(OrderInfo)
# admin.site.register(NewUser)
# admin.site.register(AccountAssetBills)


@admin.register(Trader)
class TraderAdmin(admin.ModelAdmin):
    list_display = ("name", "strategy", "lever", "trader_text")  # 需要显示的字段
    search_fields = list_display
    list_filter = ("name", "strategy", "lever")


@admin.register(AccountInfo)
class AccountInfoAdmin(admin.ModelAdmin):
    list_display = ("account_text", "trader", "api_key", "balance", "test_balance", "promoter", "is_active")  # 需要显示的字段
    search_fields = list_display
    list_filter = list_display


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "ma", "bar2", "instid", "accountinfo", "msg")  # 需要显示的字段
    search_fields = list_display
    list_filter = ("accountinfo", "name",)


@admin.register(OrderInfo)
class OrderInfoAdmin(admin.ModelAdmin):
    list_display = ("accountinfo", "side", "sz", "avgpx", "closeavgpx", "pnl",
                    "create_time", "update_time")
    search_fields = list_display
    list_filter = ("accountinfo",)
    list_editable = ("side", "sz", "avgpx", "closeavgpx", "pnl", "create_time")


@admin.register(PlaceAlgo)
class PlaceAlgoAdmin(admin.ModelAdmin):
    list_display = ("accountinfo", "instid", "posside", "side", "sz", "tptriggerpx", "tpordpx", "sltriggerpx",
                    "slordpx", "smsg")  # 需要显示的字段
    search_fields = list_display
    list_filter = ("accountinfo",)


@admin.register(NewUser)
class NewUserAdmin(admin.ModelAdmin):
    list_display = ("name", "create_time", "update_time")
    search_fields = list_display
    list_filter = list_display
