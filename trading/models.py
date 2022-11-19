from django.db import models
from django.utils import timezone
import datetime

# Create your models here.
"""
在models.py中修改模型；
python manage.py makemigrations --empty trading  重来
python manage.py makemigrations trading 为改动创建迁移记录文件；
python manage.py migrate trading 将操作同步到数据库。
"""


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.question_text

    # 是否在当前发布的问卷
    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


class Trader(models.Model):
    class Meta:
        # db_table = 'trader'
        verbose_name = "交易员"
        verbose_name_plural = "交易员"

    name = models.CharField(verbose_name="昵称", max_length=50)
    account = models.CharField(verbose_name="登陆账户", max_length=50)
    password = models.CharField(verbose_name="密码", max_length=50)
    strategy = models.CharField(max_length=50, default='MaTrade', editable=False)
    trading = models.BooleanField(default=False, editable=False)
    trader_text = models.CharField(max_length=200, null=True, editable=False)
    lever = models.IntegerField(verbose_name="交易等级", default=1, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class AccountInfo(models.Model):
    class Meta:
        verbose_name = "交易账户信息"
        verbose_name_plural = "交易账户信息"

    data = (
        ('0', '实盘'),
        ('1', '模拟'),
    )

    trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
    account_text = models.CharField(verbose_name='用户名称', max_length=50)
    api_key = models.CharField(max_length=50, unique=True)
    secret_key = models.CharField(max_length=50)
    passphrase = models.CharField(max_length=50)
    balance = models.FloatField(verbose_name='保证金（USD）', default=-1)
    init_balance = models.FloatField(verbose_name='保证金（USD）', default=-1)
    flag = models.CharField(default='0', max_length=10, choices=data, editable=False)
    email = models.CharField(max_length=50, null=True)
    phone = models.CharField(max_length=50, null=True)
    promoter = models.CharField(verbose_name='推介人姓名', max_length=50, null=True)
    status = models.IntegerField(default=0, editable=False)
    operate = models.IntegerField(default=1, editable=False)
    msg = models.TextField(null=True, blank=True, editable=False)
    strategy_name = models.CharField(max_length=20, null=True, editable=False)
    bar2 = models.CharField(max_length=10, null=True, editable=False)
    is_active = models.IntegerField(default=1, editable=False)

    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.account_text


class Strategy(models.Model):
    class Meta:
        verbose_name = "策略"
        verbose_name_plural = "策略"

    name = models.CharField(verbose_name='策略名称', max_length=50)
    is_active = models.IntegerField(default=0, editable=False)
    status = models.IntegerField(default=0, editable=False)
    ma = models.CharField(verbose_name='均线', null=True, max_length=10)
    bar2 = models.CharField(verbose_name='大周期', null=True, max_length=10)
    instid = models.CharField(verbose_name='合约', null=True, max_length=50)
    accountinfo = models.TextField(verbose_name='账户', null=True, blank=True, editable=False)
    signalinfo = models.TextField(verbose_name='信号信息', null=True, blank=True, editable=False)
    msg = models.TextField(null=True, blank=True, editable=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class OrderInfo(models.Model):
    class Meta:
        verbose_name = "订单信息"
        verbose_name_plural = "订单信息"

    accountinfo = models.ForeignKey(AccountInfo, on_delete=models.CASCADE)
    strategyid = models.IntegerField(default=0, null=True)
    ordid = models.CharField(max_length=50)
    instid = models.CharField(max_length=50)
    posside = models.CharField(max_length=10, null=True)
    side = models.CharField(max_length=10, null=True)
    avgpx = models.CharField(max_length=20, null=True)
    closeavgpx = models.CharField(max_length=20, null=True)
    tptriggerpx = models.CharField(max_length=20, null=True)
    tpordpx = models.CharField(max_length=20, null=True)
    sltriggerpx = models.CharField(max_length=20, null=True)
    slordpx = models.CharField(max_length=20, null=True)
    algoid = models.CharField(max_length=50, null=True)
    closeordid = models.CharField(max_length=50, null=True)

    tdmode = models.CharField(default='cross', max_length=20, null=True)
    ccy = models.CharField(default='USDT', max_length=20, null=True)
    ordtype = models.CharField(default='market', max_length=20, null=True)
    sz = models.CharField(default='0', max_length=20, null=True)
    px = models.CharField(max_length=20, null=True)
    accfillsz = models.CharField(max_length=20, null=True)
    pnl = models.CharField(max_length=20, null=True)
    lever = models.CharField(max_length=10, null=True)
    fee = models.CharField(max_length=10, null=True)     # 手续费

    close_position = models.IntegerField(default=0)
    status = models.IntegerField(default=0)
    msg = models.TextField(null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    # date = models.DateTimeField('date published')

    order_ctime = models.CharField(max_length=40, null=True)    # 订单创建时间
    order_utime = models.CharField(max_length=40, null=True)    # 订单更新时间
    algo_ctime = models.CharField(max_length=40, null=True)

    def __str__(self):
        return self.accountinfo


class NewUser(models.Model):
    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    name = models.CharField(verbose_name='登录名', max_length=20)
    password = models.CharField(verbose_name='密码', max_length=20)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class AccountAssetBills(models.Model):
    class Meta:
        verbose_name = "资金流水"
        verbose_name_plural = "资金流水"

    accountinfo = models.ForeignKey(AccountInfo, on_delete=models.CASCADE)
    billid = models.CharField(verbose_name='账单 ID', max_length=20, unique=True)
    bal = models.CharField(verbose_name='账户层面的余额数量', max_length=20)
    balchg = models.CharField(verbose_name='账户层面的余额变动数量', max_length=20)
    ccy = models.CharField(verbose_name='账户余额币种', max_length=20)
    type = models.CharField(verbose_name='账单类型', max_length=10, null=True)
    bill_date = models.CharField(verbose_name='时间', max_length=50)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.accountinfo


class PlaceAlgo(models.Model):
    class Meta:
        verbose_name = "策略委托订单"
        verbose_name_plural = "策略委托订单"

    accountinfo = models.ForeignKey(AccountInfo, on_delete=models.CASCADE)
    algoid = models.CharField(verbose_name='委托订单 ID', max_length=50, unique=True)
    clordid = models.CharField(verbose_name='自定义 ID', max_length=50, null=True)
    orderid = models.CharField(verbose_name='开仓 ID', max_length=50)
    strategyid = models.IntegerField(verbose_name='策略 ID', default=0)
    instid = models.CharField(max_length=50, null=True)
    posside = models.CharField(max_length=10, null=True)
    side = models.CharField(max_length=10, null=True)
    sz = models.CharField(max_length=10, null=True)

    tptriggerpx = models.CharField(max_length=20, null=True)
    tpordpx = models.CharField(max_length=20, null=True)
    sltriggerpx = models.CharField(max_length=20, null=True)
    slordpx = models.CharField(max_length=20, null=True)
    scode = models.CharField(max_length=5, null=True)
    smsg = models.TextField(null=True)

    status = models.IntegerField(default=0)

    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    algo_ctime = models.CharField(max_length=40, null=True)    # 订单创建时间

    def __str__(self):
        return self.accountinfo
