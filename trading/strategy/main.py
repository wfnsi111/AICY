# -*- coding: utf-8 -*-

from .basetrade.basetrade import BaseTrade
from importlib import import_module
from requests.exceptions import ConnectionError


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

    def start_tarde(self, strategy, **kwargs):
        self.log.info("start trading...............................")
        print('CyTrade 初始化中........')
        strategy_obj = self.choose_strategy(strategy, **kwargs)
        try:
            strategy_obj.start_my_trade()
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


if __name__ == '__main__':
    pass
