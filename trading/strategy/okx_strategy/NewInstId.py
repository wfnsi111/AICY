# -*- coding: utf-8 -*-

"""
Beta MA No.1

信号1 趋势中
信号2 大周期接近均线
信号3 小周期影线和成交量达到要求

"""
import json

from ..okx.AccountAndTradeApi import AccountAndTradeApi
from ...models import AccountInfo, Strategy, PlaceAlgo
import pandas as pd

import time
from ..basetrade.basetrade import BaseTrade

import re


class NewInstId(BaseTrade):
    def __init__(self, api_key=None, secret_key=None, passphrase=None, use_server_time=False, flag='1', **kwargs):
        super().__init__(api_key, secret_key, passphrase, use_server_time, flag, logfile=kwargs.get('logfile', None))
        self.df = None
        self.df_3mins = None
        self.stop_loss = 0
        self.flag = flag
        self.instId = kwargs.get('instId')
        self.slTriggerPx = kwargs.get('slTriggerPx')
        self.tpTriggerPx = kwargs.get('tpTriggerPx')
        self.sz = kwargs.get('sz')

        self.trader = kwargs.get('trader')
        self.accountinfo_obj = kwargs.get('accountinfo')
        self.strategy_obj = self.init_strategy(kwargs.get('strategy_obj'))
        self.all_accountinfo_data_list = None
        self.orderinfo_obj = None
        self.side_type = {"buy": "long", "sell": "short"}
        self.side = "buy"
        self.posSide = 'long'
        self.lever = "1"
        self.last_price = ''
        self.availPos = None
        self.avgpx = None
        self.signal_info_dict = {}

    def init_strategy(self, strategy_obj):
        strategy_obj.instid = self.instId
        strategy_obj.save()
        return strategy_obj

    def start_my_trade(self):
        self.all_accountinfo_data_list = self.set_initialization_account_all_by_newinstid(self.strategy_obj.accountinfo,
                                                                             self.strategy_obj.name,
                                                                             self.strategy_obj.instid,
                                                                             lever="1",
                                                                             )
        if not self.all_accountinfo_data_list:
            self.log.info('no account info data')
            return
        if self.strategy_obj.status < 5:
            self.track_trading_status(1)

        self.ready_order()

        for accountinfo in self.all_accountinfo_data_list:
            obj = accountinfo['obj']
            obj.status = 0
            obj.save()

    def ready_order(self):
        para = {
            "instId": self.instId,
            "tdMode": self.tdMode,
            "ccy": 'USDT',
            'side': "buy",
            'ordType': 'market',
            'px': '',
        }
        place_order_code = False
        place_order_error_code = False
        placc_algo_order_info_list = []
        for accountinfo in self.all_accountinfo_data_list:
            orderinfo_dict = {}
            obj = accountinfo['obj']
            obj_api = accountinfo['obj_api']
            orderinfo_dict['lever'] = self.lever
            para['sz'] = self.sz
            orderinfo_dict.update(para)
            while True:
                result = obj_api.tradeAPI.place_order(**para)
                ordId, sCode, sMsg = self.check_order_result_data(result, 'ordId')
                print(sMsg)
                if "Instrument ID doesn't exist" != sMsg:
                    break

            if sCode == "0":
                accountinfo['status'] = 2
                place_order_code = True
                # 获取持仓信息
                # self.get_order_details(self.instId, ordId)
                self.has_order = self.get_positions(instType='MARGIN')
                self.order_times += 1
                print('%s 开仓成功！！！！！！' % obj.account_text)
                self.log.info('%s 开仓成功！！！！！！' % obj.account_text)
                # self.track_trading_status(5)

                if self.order_lst:
                    self.avgpx = float(self.order_lst[0].get('avgPx'))
                    self.availPos = float(self.order_lst[0].get('availPos'))    # 可平仓数量，
                    orderinfo_dict['order_ctime'] = self.timestamp_to_date(self.order_lst[0].get('cTime'))
                    orderinfo_dict['order_utime'] = self.timestamp_to_date(self.order_lst[0].get('uTime'))
                else:
                    result = self.marketAPI.get_ticker(self.instId)
                    for data in result.get('data'):
                        self.last_price = data.get("last")
                    self.avgpx = self.last_price

                orderinfo_dict['ordId'] = ordId
                orderinfo_dict['avgPx'] = self.avgpx

                # 设置止损止盈
                algo_para = self.set_place_algo_order_oco(obj_api, self.sz)
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
        side = 'sell'
        self.tpTriggerPx = float(self.avgpx) * float(self.tpTriggerPx) if self.tpTriggerPx else float(self.avgpx) * 5
        self.slTriggerPx = float(self.avgpx) * float(self.slTriggerPx) if self.slTriggerPx else float(self.avgpx) * 0.7
        price_para = {
            "tpTriggerPx": self.tpTriggerPx,
            "tpOrdPx": "-1",
            "slTriggerPx": self.slTriggerPx,
            "slOrdPx": "-1"
        }
        try:
            result = obj_api.tradeAPI.place_algo_order(self.instId, self.tdMode, side, ordType=self.ordType,
                                                       sz=self.availPos, **price_para, ccy='USDT',
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
            msg = "止损止盈设置错误，，，%s, 止损：%s, 止盈：%s, 现价：%s" % (
                msg, self.slTriggerPx, self.tpTriggerPx, self.last_price)
            self.log.error(msg)

        price_para['algoid'] = algoId
        price_para['posside'] = self.posSide
        price_para['side'] = side
        price_para['sz'] = sz
        price_para['scode'] = sCode
        price_para['smsg'] = msg
        price_para['status'] = status
        return price_para

    def set_initialization_account_all_by_newinstid(self, all_accountinfo, strategy_name, instid, interval=0.2, lever='50',
                                       mgnMode='cross'):
        # 初始化状态， 设置倍数， 账户状态。
        all_accountinfo_obj = AccountInfo.objects.filter(pk__in=all_accountinfo)
        all_accountinfo_data_list = []
        for obj in all_accountinfo_obj:
            if interval:
                time.sleep(interval)
            accountinfo_data = {}
            try:
                obj_api = AccountAndTradeApi(obj.api_key, obj.secret_key, obj.passphrase, False, obj.flag)
                # try:
                #     result = self.accountAPI.set_leverage(instId=self.instId, lever=lever, mgnMode=mgnMode)
                #     result = self.accountAPI.get_position_mode('long_short_mode')
                # except Exception as e:
                #     print(e)
                #     print('初始化账户 error')
                balance = obj_api.get_my_balance('availEq')
                obj.balance = float(balance)
                if obj.init_balance == -1:
                    obj.init_balance = float(balance)
                obj.strategy_name = strategy_name
                obj.status = 1
                accountinfo_data['id'] = obj.id
                accountinfo_data['name'] = obj.account_text
                accountinfo_data['balance'] = balance
                accountinfo_data['obj'] = obj
                accountinfo_data['obj_api'] = obj_api
                all_accountinfo_data_list.append(accountinfo_data)
            except Exception as e:
                obj.status = -1
                self.log.error('set_initialization_account_all error')
                self.log.error(e)
            obj.save()
        return all_accountinfo_data_list