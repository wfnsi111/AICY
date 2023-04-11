# -*- coding: utf-8 -*-

"""
Beta MA No.1

信号1 趋势中
信号2 大周期接近均线
信号3 小周期影线和成交量达到要求

"""
import json

from ...models import AccountInfo, Strategy, PlaceAlgo
import pandas as pd

import time
from ..basetrade.basetrade import BaseTrade

import re


class LaoZhang(BaseTrade):
    def __init__(self, api_key=None, secret_key=None, passphrase=None, use_server_time=False, flag='1', **kwargs):
        super().__init__(api_key, secret_key, passphrase, use_server_time, flag, logfile=kwargs.get('logfile', None))
        self.df = None
        self.df_3mins = None
        self.stop_loss = 0
        self.flag = flag
        self.instId = kwargs.get('instId')
        self.slTriggerPx = kwargs.get('slTriggerPx')
        self.tpTriggerPx = kwargs.get('tpTriggerPx')
        # self.risk_control = kwargs.get('risk')
        self.risk_control = 0.02
        self.side = kwargs.get('side')
        self.trader = kwargs.get('trader')
        self.accountinfo_obj = kwargs.get('accountinfo')
        self.strategy_obj = self.init_strategy(kwargs.get('strategy_obj'))
        self.all_accountinfo_data_list = None
        self.orderinfo_obj = None
        self.side_type = {"buy": "long", "sell": "short"}
        self.lever = "50"
        self.last_price = ''
        self.avgpx = None
        self.signal_info_dict = {}

    def init_strategy(self, strategy_obj):
        strategy_obj.instid = self.instId
        strategy_obj.save()
        return strategy_obj

    def start_my_trade(self):
        self.all_accountinfo_data_list = self.set_initialization_account_all(self.strategy_obj.accountinfo,
                                                                             self.strategy_obj.name,
                                                                             self.strategy_obj.instid,
                                                                             )
        if not self.all_accountinfo_data_list:
            self.log.info('no account info data')
            return
        if self.strategy_obj.status < 5:
            self.track_trading_status(1)

        result = self.marketAPI.get_ticker(self.instId)
        for data in result.get('data'):
            self.last_price = data.get("last")
            print(self.last_price)

        self.ready_order()

        for accountinfo in self.all_accountinfo_data_list:
            obj = accountinfo['obj']
            obj.status = 0
            obj.save()

    def ready_order(self):
        self.posSide = self.side_type.get(self.side)
        para = {
            "instId": self.instId,
            "tdMode": self.tdMode,
            "ccy": 'USDT',
            'side': self.side,
            'ordType': 'market',
            'px': '',
            'posSide': self.posSide
        }
        place_order_code = False
        place_order_error_code = False
        placc_algo_order_info_list = []
        for accountinfo in self.all_accountinfo_data_list:
            orderinfo_dict = {}
            obj = accountinfo['obj']
            obj_api = accountinfo['obj_api']
            orderinfo_dict['lever'] = self.lever
            sz, org_sz = self.set_my_position(accountinfo['balance'], self.slTriggerPx, self.last_price)
            para['sz'] = sz
            orderinfo_dict.update(para)

            if not sz:
                msg = '仓位太小， 无法开仓 ---> *** 余额%sU ***' % accountinfo['balance']
                self.log.error(accountinfo['name'])
                self.log.error(msg)
                accountinfo['msg'] = msg
                continue

            result = obj_api.tradeAPI.place_order(**para)
            # result = self.tradeAPI.place_order(**para)
            ordId, sCode, sMsg = self.check_order_result_data(result, 'ordId')
            if sCode == "0":
                accountinfo['status'] = 2
                place_order_code = True
                # 获取持仓信息
                # self.get_order_details(self.instId, ordId)
                self.has_order = self.get_positions()
                self.order_times += 1
                print('%s 开仓成功！！！！！！' % obj.account_text)
                self.log.info('%s 开仓成功！！！！！！' % obj.account_text)
                # self.track_trading_status(5)

                self.avgpx = self.last_price
                if self.order_lst:
                    self.avgpx = "%.2f" % float(self.order_lst[0].get('avgPx'))
                    orderinfo_dict['order_ctime'] = self.timestamp_to_date(self.order_lst[0].get('cTime'))
                    orderinfo_dict['order_utime'] = self.timestamp_to_date(self.order_lst[0].get('uTime'))

                orderinfo_dict['ordId'] = ordId
                orderinfo_dict['avgPx'] = self.avgpx

                # 设置止损止盈
                algo_para = self.set_place_algo_order_oco(obj_api, sz)
                algo_para['orderid'] = ordId
                algo_para['accountinfo_id'] = obj.id
                algo_para['instid'] = self.instId
                placc_algo_order_info_list.append(algo_para)
                orderinfo_dict.update(algo_para)
                orderinfo_dict['posside'] = self.posSide
                orderinfo_dict['side'] = self.side
                self.has_order = True
            else:
                place_order_error_code = True
                # self.track_trading_status(-1)
                msg = '%s 账户异常！！！开仓失败！！！！！！' % obj.account_text
                accountinfo['status'] = -1
                accountinfo['msg'] = msg
                self.log.error(msg)
                self.has_order = False
            accountinfo['orderinfo'] = orderinfo_dict

        if place_order_code:
            self.has_order = True
            self.track_trading_status(5)
            # 发消息提示
            # self.send_msg_to_me(self.trader)
        if place_order_error_code:
            self.track_trading_status(6)

        # 保存订单信息
        for accountinfo in self.all_accountinfo_data_list:
            orderinfo_dict = accountinfo['orderinfo']
            orderinfo_dict['strategyid'] = self.strategy_obj.id
            accountinfo_obj = accountinfo['obj']

            # 保存订单信
            orderinfo_obj = self.set_trading_orderinfo(accountinfo_obj, **orderinfo_dict)
            accountinfo['orderinfo_obj'] = orderinfo_obj

            # 保存账户状态
            accountinfo_obj.status = accountinfo['status']
            accountinfo_obj.save()

        # 保存策略信息
        self.signal_info_dict['posSide'] = self.posSide
        self.signal_info_dict['instId'] = self.instId
        self.signal_info_dict['side'] = self.side
        self.signal_info_dict['avgPx'] = self.avgpx
        self.signal_info_dict['stop_loss_price'] = self.slTriggerPx
        self.set_strategy_info(self.signal_info_dict)

        # 保存委托订单信息
        for item in placc_algo_order_info_list:
            new_dict = {}
            for i, j in item.items():
                # 把key转小写
                new_dict[i.lower()] = j
            algo = PlaceAlgo(**new_dict, strategyid=self.strategy_obj.id)
            try:
                algo.save()
            except Exception as e:
                print(e)

    def track_trading_status(self, status=0, update_status=True):
        strategy_obj = Strategy.objects.get(pk=self.strategy_obj.id)
        if strategy_obj.status in (0, -2):
            self.log.info('已强行停止策略')
            raise Exception('已强行停止策略')
        if update_status:
            self.strategy_obj.status = status
            self.strategy_obj.save()
            self.log.info('更新运行状态--%s--' % status)

    def set_my_position(self, mybalance, slTriggerPx, last_price):
        """ 通过止损和现价 确认仓位 """
        p = abs(float(slTriggerPx) - float(last_price))
        risk_price = float(mybalance) * float(self.risk_control)
        coefficient = self.get_instid_coefficient(self.instId)
        org_sz = risk_price / p
        sz = org_sz * coefficient
        if sz < 1:
            sz = 0
        return int(sz), int(org_sz)

    def set_strategy_info(self, data):
        signalinfo = self.strategy_obj.signalinfo
        if signalinfo:
            try:
                signalinfo = json.loads(signalinfo)
            except Exception as e:
                pass
                # self.log.info(e)
                # self.log.info(signalinfo)
            if isinstance(signalinfo, list):
                signalinfo.append(data)
            else:
                signalinfo = [data]
        else:
            signalinfo = [data]
        self.strategy_obj.signalinfo = signalinfo
        self.strategy_obj.save()

    def set_place_algo_order_oco(self, obj_api, sz):
        side = {"long": "sell", "short": "buy"}.get(self.posSide)
        price_para = {
            "tpTriggerPx": self.tpTriggerPx,
            "tpOrdPx": "-1",
            "slTriggerPx": self.slTriggerPx,
            "slOrdPx": "-1"
        }
        try:
            result = obj_api.tradeAPI.place_algo_order(self.instId, self.tdMode, side, ordType=self.ordType,
                                                       sz=sz, posSide=self.posSide, **price_para,
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
            # 可能是止损设置错误
            status = -1
            msg = "止损止盈设置错误，，，%s" % msg
            self.log.error(msg)

        price_para['algoid'] = algoId
        price_para['posside'] = self.posSide
        price_para['side'] = side
        price_para['sz'] = sz
        price_para['scode'] = sCode
        price_para['smsg'] = msg
        price_para['status'] = status
        return price_para

