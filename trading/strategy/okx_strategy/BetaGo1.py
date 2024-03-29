# -*- coding: utf-8 -*-

"""
Beta Angel No.1

开仓：
1 成交量大于等于该周期成交量60MA的3倍
2 下影线长度大于等于上影线长度的1.5倍
3 下影线长度大于等于实体长度0.66倍

平仓：
1 成交量大于等于该周期成交量60MA的3倍
2 下影线长度大于等于上影线长度的1.5倍

"""
import json
import random

from ...models import AccountInfo, Strategy, PlaceAlgo

import time
from ..basetrade.basetrade import BaseTrade


class BetaGo1(BaseTrade):
    def __init__(self, api_key=None, secret_key=None, passphrase=None, use_server_time=False, flag='1', **kwargs):
        super().__init__(api_key, secret_key, passphrase, use_server_time, flag, logfile=kwargs.get('logfile', None))
        self.df = None
        self.KL = None
        self.flag = flag
        self.instId = kwargs.get('instId')
        self.bar2 = kwargs.get('bar2')
        self.trader = kwargs.get('trader')
        self.accountinfo_obj = kwargs.get('accountinfo')
        self.strategy_obj = self.init_strategy(kwargs.get('strategy_obj'))
        self.all_accountinfo_data_list = None
        self.orderinfo_obj = None
        self.signal_order_para = None
        self.signal_info_dict = {}
        self.lever = "50"
        self.signal_recorder = {}
        self.last_price = ''
        self.stop_loss_price = 0
        self.vol_ma = 60
        self.order_posside = None
        self.avgpx = None
        self.risk_control = 0.01

    def init_strategy(self, strategy_obj):
        strategy_obj.instid = self.instId
        strategy_obj.bar2 = self.bar2
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
        while True:
            time.sleep(1)
            self.track_trading_status(update_status=False)
            self.df = self._get_market_data(self.instId, self.bar2, vol_ma=self.vol_ma)
            self.KL = self.df.iloc[-1, :]

            signal1 = self.check_signal1()
            # signal1 = True
            if signal1:
                signal2 = self.check_signal2()
                # signal2 = random.choice(['down_wick_flag', 'up_wick_flag'])
                if signal2:
                    # 判断是开仓还是平仓
                    code = self.check_order_status(signal2)
                    if code == 0:
                        continue

                    signal3 = self.check_signal3(signal2)
                    # signal3 = True
                    if signal3:
                        self.log.info(self.signal_recorder)
                        self.log.info('满足信号 ，准备开仓')
                        self.track_trading_status(4)
                        self.ready_order()

    def check_order_status(self, signal2):
        # 如果有持仓，判断信号是否为平仓信号
        code = 1
        self.has_order = self.get_positions()
        if self.has_order:
            code = 0
            for order in self.order_lst:
                instId = order.get("instId")
                mgnMode = order.get('mgnMode')
                posSide = order.get('posSide')
                ccy = order.get('ccy')
                self.order_posside = order.get('posSide')
                if signal2 == 'down_wick_flag':
                    # 出现做多的信号
                    if self.order_posside == 'long':
                        # 有多单的持仓，就不操作
                        code = 0
                    else:
                        # 有空单的持仓，止盈平仓
                        code = 1
                        # self.stop_order(instId, mgnMode, posSide, ccy)
                        status_lst = self.stop_order_all(instId, mgnMode, posSide, ccy)
                        if -1 in status_lst:
                            pass
                        else:
                            # 平仓完成，重置运行状态
                            self.track_trading_status(1)
                else:
                    # 出现做空的信号
                    if self.order_posside == 'long':
                        # 有多单的持仓，止盈平仓
                        code = 1
                        status_lst = self.stop_order_all(instId, mgnMode, posSide, ccy)
                        if -1 in status_lst:
                            pass
                        else:
                            # 平仓完成，重置运行状态
                            self.track_trading_status(1)
                    else:
                        # 有空单的持仓，就不操作
                        code = 0
        return code

    def stop_order(self, instId, mgnMode, posSide, ccy):
        self.close_positions_one(instId, mgnMode, posSide)

    def stop_order_all(self, instId, mgnMode, posSide, ccy):
        # 平仓
        self.log.info('准备平仓')
        status_lst = []
        for accountinfo in self.all_accountinfo_data_list:
            obj = accountinfo['obj']
            obj_api = accountinfo['obj_api']
            para = {
                "instId": instId,
                'mgnMode': mgnMode,
                "ccy": ccy,
                "posSide": posSide,
                'autoCxl': True,
                "clOrdId": "1111",
            }
            try:
                result = obj_api.tradeAPI.close_positions(**para)
                if result.get("code") == '0':
                    self.log.info('平仓成功')
                    status = 0
                else:
                    status = -1
            except Exception as e:
                print(self.log.error(e))
                status = -1
            status_lst.append(status)

        # 保存信息
        for accountinfo in self.all_accountinfo_data_list:
            orderinfo_dict = {}
            obj = accountinfo['obj']
            obj_api = accountinfo['obj_api']
            orderinfo_obj = accountinfo.get('orderinfo_obj', None)
            if not orderinfo_obj:
                continue
            count_time = 0
            while True:
                # 循环获取 ，避免交易所的延迟造成的未获取订单信息
                count_time += 1
                time.sleep(0.1)
                result = obj_api.tradeAPI.get_orders_history('SWAP', limit='1')
                order_data = result.get('data')[0]
                if count_time == 10:
                    break
                if order_data.get('ordId') == orderinfo_obj.ordid:
                    continue
                pnl = order_data.get('pnl')
                orderinfo_obj.pnl = pnl
                orderinfo_obj.closeavgpx = "%.2f" % float(order_data.get('avgPx'))
                orderinfo_obj.closeordid = order_data.get('ordId')
                orderinfo_obj.close_position = 1
                orderinfo_obj.save()
                count_time = 0
                break

        return status_lst

    def check_signal1(self, pro=3):
        # 1 成交量大于等于该周期成交量60MA的3倍
        self.track_trading_status(update_status=False)
        signal1 = False
        last_p = float(self.KL['close'])
        volume = float(self.KL['volume'])
        ma_vol = float(self.KL['vol_ma'])

        if volume >= ma_vol * pro:
            signal1 = True
            self.signal_recorder["signal1"] = {'bar2': self.bar2, 'last': last_p, 'volume': volume,
                                               'ma_vol': ma_vol}
        return signal1

    def check_signal2(self, pro=1.5):
        self.track_trading_status(update_status=False)
        # 下影线长度大于等于上影线长度的1.5倍
        _open = float(self.KL['open'])
        _close = float(self.KL['close'])
        _high = float(self.KL['high'])
        _low = float(self.KL['low'])
        down_wick = min(_close, _open) - _low
        up_wick = _high - max(_close, _open)
        if down_wick >= pro * up_wick:
            # 下影线长度大于等于上影线长度的1.5倍
            signal2 = 'down_wick_flag'
        elif up_wick >= pro * down_wick:
            # 上影线长度大于等于下影线长度的1.5倍
            signal2 = 'up_wick_flag'
        else:
            signal2 = False
        self.signal_recorder["signal2"] = {'_open': _open, '_close': _close, '_high': _high, '_low': _low,
                                           "down_wick": down_wick, "up_wick": up_wick}
        return signal2

    def check_signal3(self, signal2, pro=0.66):
        # 影线长度大于等于实体长度0.66倍
        self.track_trading_status(update_status=False)
        _open = float(self.KL['open'])
        _close = float(self.KL['close'])
        _high = float(self.KL['high'])
        _low = float(self.KL['low'])
        entity = abs(_close - _open)
        down_wick = min(_close, _open) - _low
        up_wick = _high - max(_close, _open)
        if signal2 == 'down_wick_flag':
            # 下影线长度大于等于实体长度0.66倍
            signal3 = True if down_wick >= entity * pro else False
            self.signal_order_para = {"side": "buy", "posSide": "long"}
            self.stop_loss_price = _low
        else:
            # 上影线长度大于等于实体长度0.66倍
            signal3 = True if up_wick >= entity * pro else False
            self.signal_order_para = {"side": "sell", "posSide": "short"}
            self.stop_loss_price = _high

        self.signal_recorder["signal3"] = {"down_wick": down_wick, "up_wick": up_wick, "entity": entity}
        return signal3

    def ready_order(self):
        self.posSide = self.signal_order_para.get('posSide')
        self.side = self.signal_order_para.get('side')
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
            sz, org_sz = self.set_my_position(accountinfo['balance'])
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
                algo_para = self.set_place_algo_order_oco(obj_api, sz, self.avgpx, org_sz, accountinfo['balance'])
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
            self.send_msg_to_me(self.trader)
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
        self.signal_info_dict['stop_loss_price'] = self.stop_loss_price
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

        # 等1根 K线
        t = int(self.bar2[:-1]) * 60 if "m" in self.bar2 else int(self.bar2[:-1]) * 60 * 60
        self.log.info('开仓完成，等待1根K线收线--%s' % self.bar2)
        for i in range(t // 5):
            time.sleep(5)
            self.track_trading_status(update_status=False)

    def track_trading_status(self, status=0, update_status=True):
        strategy_obj = Strategy.objects.get(pk=self.strategy_obj.id)
        if strategy_obj.status in (0, -2):
            self.log.info('已强行停止策略')
            raise Exception('已强行停止策略')
        if update_status:
            self.strategy_obj.status = status
            self.strategy_obj.save()
            self.log.info('更新运行状态--%s--' % status)

    def set_my_position(self, mybalance):
        """
        做空： 总资金*1%风险值/ (收盘价减去最高价的绝对值)
        做多： 总资金*1%风险值/ (收盘价减去最低价的绝对值)

        """

        _close = float(self.KL['close'])
        _high = float(self.KL['high'])
        _low = float(self.KL['low'])
        org_sz = float(mybalance) * self.risk_control / abs(_close - (_low if self.posSide == 'long' else _high))
        sz = self.currency_to_sz(self.instId, org_sz)
        if sz < 1:
            sz = 0
        return int(sz), int(org_sz)

    def set_place_algo_order_oco(self, obj_api, sz, avgpx, org_sz, balance):
        side = {"long": "sell", "short": "buy"}.get(self.posSide)
        p_pre1 = self.reset_algo_order_price(balance, org_sz)
        price_para, sl2 = self.set_place_algo_order_price(avgpx, self.posSide, p_pre1)
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
            price_para['slTriggerPx'] = sl2
            result = obj_api.tradeAPI.place_algo_order(self.instId, self.tdMode, side, ordType=self.ordType,
                                                       sz=sz, posSide=self.posSide, **price_para,
                                                       tpTriggerPxType='last', slTriggerPxType='last')
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

    def reset_algo_order_price(self, balance, org_sz):
        p_pre1 = float(balance) * self.risk_control / float(org_sz)    # p为止损1%的点数
        return p_pre1

    def set_place_algo_order_price(self, avgPx, posSide, p_pre1):
        # K线收盘的最低价
        if posSide == 'long':
            tp = float(avgPx) * 1.2
            sl = self.stop_loss_price
            sl2 = self.stop_loss_price - p_pre1
        else:
            tp = float(avgPx) * 0.8
            sl = self.stop_loss_price
            sl2 = self.stop_loss_price + p_pre1
        # -1 为市价平仓
        p2 = "-1"
        price_para = {
            "tpTriggerPx": "%0.2f" % tp,
            "tpOrdPx": p2,
            "slTriggerPx": "%0.2f" % sl,
            "slOrdPx": p2
        }
        return price_para, sl2

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