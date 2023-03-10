# -*- coding: utf-8 -*-

"""
理想状态：
54秒启动
55秒开仓
"""
import json

from ...models import AccountInfo, Strategy, PlaceAlgo
import time
from ..basetrade.basetrade import BaseTrade
from ..conf.ma_trade_args import args_dict
import re


class HedgeTransaction(BaseTrade):
    def __init__(self, api_key=None, secret_key=None, passphrase=None, use_server_time=False, flag='1', **kwargs):
        super().__init__(api_key, secret_key, passphrase, use_server_time, flag, logfile=kwargs.get('logfile', None))
        self.flag = flag
        self.instId = kwargs.get('instId')
        self.sz = kwargs.get('sz')
        self.trader = kwargs.get('trader')
        self.lever = kwargs.get('lever')
        self.mgnMode = kwargs.get('mgnMode')
        self.algo_tp = kwargs.get('algo_tp', None)
        self.algo_sl = kwargs.get('algo_sl', None)
        self.first = kwargs.get('first', None)
        self.accountinfo_obj = kwargs.get('accountinfo')
        self.strategy_obj = kwargs.get('strategy_obj')
        self.avgpx = None

    def start_my_trade(self):
        self.all_accountinfo_data_list = self.set_initialization_account_all(self.strategy_obj.accountinfo,
                                                                             self.strategy_obj.name,
                                                                             self.strategy_obj.instid,
                                                                             interval=0,
                                                                             lever=self.lever,
                                                                             mgnMode=self.mgnMode,
                                                                             )

        self.ready_order()

    def ready_order(self):
        buy_para = {
            "instId": self.instId,
            "tdMode": self.mgnMode,
            "ccy": 'USDT',
            'side': "buy",
            'ordType': 'market',
            'px': '',
            'posSide': "long",
            'sz': self.sz,
        }

        sell_para = {
            "instId": self.instId,
            "tdMode": self.mgnMode,
            "ccy": 'USDT',
            'side': 'sell',
            'ordType': 'market',
            'px': '',
            'posSide': "short",
            'sz': self.sz,
        }
        para_lst = [buy_para, sell_para] if self.first == 'buy' else [sell_para, buy_para]
        for index, accountinfo in enumerate(self.all_accountinfo_data_list):
            obj = accountinfo['obj']
            obj_api = accountinfo['obj_api']
            # for para in para_lst:
            para = para_lst[index]
            result = obj_api.tradeAPI.place_order(**para)
            # result = self.tradeAPI.place_order(**para)
            ordId, sCode, sMsg= self.check_order_result_data(result, 'ordId')
            if sCode == "0":
                accountinfo['status'] = 2
                # 获取持仓信息
                self.has_order = self.get_positions()
                self.log.info('%s 开仓成功！！！！！！' % obj.account_text)
                if not self.avgpx:
                    self.avgpx = "%.2f" % float(self.order_lst[0].get('avgPx'))

                # 设置止损止盈
                posSide = para.get("posSide")
                self.set_place_algo_order_oco(obj_api, posSide, self.sz, self.avgpx)
                self.has_order = True
            else:
                msg = '%s 账户异常！！！开仓失败！！！！！！' % obj.account_text
                self.log.error(msg)
                self.has_order = False

    def set_place_algo_order_oco(self, obj_api, posSide, sz, avgpx):
        side = {"long": "sell", "short": "buy"}.get(posSide)

        price_para = self.set_place_algo_order_price(avgpx, posSide)

        try:
            result = obj_api.tradeAPI.place_algo_order(self.instId, self.mgnMode, side, ordType=self.ordType,
                                                       sz=sz, posSide=posSide, **price_para,
                                                       tpTriggerPxType='last', slTriggerPxType='last')
        except Exception as e:
            self.log.error("委托单错误")
            self.log.error(e)
            return
        algoId, sCode, msg = self.check_order_result_data(result, "algoId")
        if sCode == "0":
            # 事件执行结果的code，0代表成功
            status = 1
            self.log.info("止损止盈设置成功 市价委托")
            try:
                result = obj_api.tradeAPI.order_algos_list(ordType=self.ordType, algoId=algoId, instType='SWAP')
                price_para['algo_ctime'] = self.timestamp_to_date(result.get('data')[0].get('cTime'))
            except Exception as e:
                self.log.error(e)
        else:
            # 事件执行失败时的msg
            status = -1
            msg = "止损止盈设置错误，，，%s" % msg
            self.log.error(msg)

    def set_place_algo_order_price(self, avgPx, posSide):
        if not self.algo_sl:
            self.algo_sl = 5
        if posSide == 'long':
            tp = float(avgPx) + int(self.algo_tp)
            sl = float(avgPx) - int(self.algo_sl)
        else:
            tp = float(avgPx) - int(self.algo_tp)
            sl = float(avgPx) + int(self.algo_sl)

        # -1 为市价平仓
        p2 = "-1"
        price_para = {
            "tpTriggerPx": "%0.2f" % tp,
            "tpOrdPx": p2,
            "slTriggerPx": "%0.2f" % sl,
            "slOrdPx": p2
        }
        return price_para