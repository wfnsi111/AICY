# -*- coding: utf-8 -*-

from .basetrade.basetrade import BaseTrade
from importlib import import_module
from requests.exceptions import ConnectionError
from ..models import Strategy, AccountInfo


class MyTrade(BaseTrade):
    def __init__(self, api_key, secret_key, passphrase, use_server_time=False, flag="1"):
        super().__init__(api_key, secret_key, passphrase, use_server_time, flag)
        self.passphrase = passphrase
        self.api_key = api_key
        self.secret_key = secret_key
        self.use_server_time = use_server_time
        self.flag = flag
        self.side = 'buy'
        self.trade_ok = False
        self.posSide = ''
        self.sz = "2"
        self.order_details = None
        self.tdMode = 'cross'
        self.ordType = 'oco'
        self.has_order = False  # 设置一个参数，只持仓1笔交易， 有持仓的时候 就不在开仓

    def start_tarde(self, strategy_name, **kwargs):
        self.log.info("start trading...............................")
        print('CyTrade 初始化中........')
        my_strategy = self.choose_strategy(strategy_name, **kwargs)
        try:
            my_strategy.start_my_trade()
        except ConnectionError as e:
            print('网络异常')
            raise ConnectionError(e)
        except Exception as e:
            self.log.error(e)
            raise Exception(e)

    def choose_strategy(self, strategy='', **kwargs):
        m_name = 'trading.strategy.okx_strategy.%s' % strategy
        module = import_module(m_name)
        cls = getattr(module, strategy)
        obj = cls(self.api_key, self.secret_key, self.passphrase, self.use_server_time, self.flag, **kwargs)
        return obj


def start_my_strategy(strategy_name, kwargs):
    all_accountinfo = kwargs.get('accountinfo')
    # 选择一个账户作为模板
    accountinfo_id = all_accountinfo[0]
    one_accountinfo = AccountInfo.objects.get(pk=accountinfo_id)
    api_key = one_accountinfo.api_key
    secret_key = one_accountinfo.secret_key
    passphrase = one_accountinfo.passphrase
    flag = one_accountinfo.flag
    use_server_time = False

    strategy_obj = Strategy(name=strategy_name, ma=kwargs.get('ma'), instid=kwargs.get('instId'),
                            bar2=kwargs.get('bar2'), accountinfo=all_accountinfo)

    kwargs['strategy_obj'] = strategy_obj
    kwargs['accountinfo'] = one_accountinfo

    try:
        strategy_obj.is_active = 1
        strategy_obj.status = 1
        strategy_obj.msg = ''
        strategy_obj.save()
        my_trade = MyTrade(api_key, secret_key, passphrase, use_server_time, flag)
        my_trade.start_tarde(strategy_name, **kwargs)
    except ConnectionError as e:
        strategy_obj.msg = e
    except Exception as e:
        print(e)
        # if strategy_obj.status == -2:
        #     strategy_obj.msg = e

    strategy_obj.status = 0
    strategy_obj.is_active = 0
    strategy_obj.save()
