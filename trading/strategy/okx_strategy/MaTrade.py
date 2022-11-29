# -*- coding: utf-8 -*-

"""

信号1 趋势中
信号2 大周期接近均线
信号3 小周期影线和成交量达到要求

"""
import json

from ...models import AccountInfo, Strategy, PlaceAlgo
import pandas as pd
try:
    import mplfinance as mpf
except:
    pass
import time
from ..basetrade.basetrade import BaseTrade
from ..conf.ma_trade_args import args_dict
import re


class MaTrade(BaseTrade):
    def __init__(self, api_key=None, secret_key=None, passphrase=None, use_server_time=False, flag='1', **kwargs):
        super().__init__(api_key, secret_key, passphrase, use_server_time, flag, logfile=kwargs.get('logfile', None))
        self.df = None
        self.df_3mins = None
        self.stop_loss = 0
        self.flag = flag
        self.ma = kwargs.get('ma')
        self.instId = kwargs.get('instId')
        self.bar2 = kwargs.get('bar2')
        self.big_bar_time = 10
        self.accountinfo_obj = kwargs.get('accountinfo')
        self.strategy_obj = kwargs.get('strategy_obj')
        self.all_accountinfo_data_list = None
        self.orderinfo_obj = None
        self.signal_order_para = None
        self.signal1 = False
        self.signal2 = False
        self.signal3 = False
        self.signal_info_dict = {}
        self.ma_percent, self.bar1, self.max_stop_loss, self.set_profit, self.risk_control = self.set_args(self.bar2)
        self.lever = "50"
        self.matrade_open_order = kwargs.get('posside', None)   # 直接开仓
        self.signal_recorder = {}
        self.last_price = ''


    def drow_k(self, df, ma_list=None):
        ma_list = [self.ma]
        title = 'MY_test'
        # 设置颜色, edge的意思是设置K线边框的颜色，默认是黑色，
        # edge=’inherit’的意思是保持K线边框的颜色与K线实体颜色一致,
        # volume=’inherit’意思是将成交量柱状图的颜色设置为红涨绿跌，与K线一致。wick 引线
        my_color = mpf.make_marketcolors(up='red', down='green', edge='inherit', wick='inherit', volume='inherit')
        my_style = mpf.make_mpf_style(marketcolors=my_color)
        # 添加均线指标
        # 添加买卖点
        # marker参数用来设定交易信号图标的形状，marker=’^’表示向上的箭头， marker=’v’表示向下的箭头， marker=’o’表示圆圈。
        # color参数可以用来控制颜色，color=’g’表示绿色（green）, ‘y’表示黄色（yellow）， ‘b’表示蓝色（blue），可以根据自己的偏好设定不同的颜色。
        args_list = [mpf.make_addplot(df[ma_list])]
        args_list.append(mpf.make_addplot(df['signal_short'], scatter=True, markersize=80, marker="v", color='r'))
        # args_list.append(mpf.make_addplot(df['signal_long'], scatter=True, markersize=80, marker="v", color='r'))
        add_plot = args_list
        # 画K线
        mpf.plot(df, type='candle', addplot=add_plot, title=title, ylabel='prise(usdt)', style=my_style, volume=True, ylabel_lower='volume')
        # mpf.plot(df, type='candle', addplot=add_plot, title=title, ylabel='prise(usdt)', style=my_style)

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
        self.has_order = self.get_positions()
        while True:
            self.signal_info_dict = {}
            if self.matrade_open_order:
                time.sleep(1)
            else:
                time.sleep(60)
            # 检测持仓
            # self.has_order = True
            if self.has_order:
                self.has_order, code = self.stop_order(profit=self.set_profit)
                if code == 1:
                    # 止盈， 结束程序
                    self.track_trading_status(0)
                    break

            if self.stop_loss == self.max_stop_loss:
                # 止损了2次， 退出程序
                self.log.info('止损%s次，退出程序' % self.max_stop_loss)
                print('止损%s次，退出程序' % self.max_stop_loss)
                self.track_trading_status(0)
                break

            if self.stop_loss < self.max_stop_loss and self.stop_loss > 0:
                # 止损了1次， 直接检测信号3
                if self.matrade_open_order:
                    break
                self.signal_info_dict = {}
                self.track_trading_status(3)
                self.signal_order_para = self.check_signal3(self.signal1)
                if self.signal_order_para:
                    if self.signal_order_para == 'no singnal':
                        # 未出现开仓信号， 停止交易
                        break
                    print()
                    print('已检测到信号3.。。。')
                    # 开仓
                    self.track_trading_status(4)
                    self.ready_order()
                    continue

            # 判断信号1
            # self.track_trading_status(1)
            self.signal1 = self.check_signal1()
            if not self.signal1:
                # print('等待信号1....................')
                continue

            self.signal_recorder["signal1"] = {"signal1": self.signal1}
            self.log.info('信号1已确认!')
            self.log.info(self.signal_recorder['signal1'])
            # 判断信号2
            self.track_trading_status(2)
            self.signal2 = self.check_signal2()
            if self.signal2:
                self.log.info("信号2已确认！")
                self.log.info(self.signal_recorder['signal2'])
                self.track_trading_status(3)
                self.signal_order_para = self.check_signal3(self.signal1)
                if self.signal_order_para:
                    if self.signal_order_para == 'no singnal':
                        # 未出现开仓信号， 停止交易
                        break
                    # 开仓
                    self.track_trading_status(4)
                    self.ready_order()

        # 结束循环，重置账户状态
        self.log.info('结束策略，重置账户状态')
        for accountinfo in self.all_accountinfo_data_list:
            obj = accountinfo['obj']
            obj.status = 0
            obj.save()

    def set_my_position(self, mybalance, atr):
        # 设置头寸
        currency = self.risk_control * float(mybalance) / atr
        sz = self.currency_to_sz(self.instId, currency)
        if sz < 1:
            sz = 0
        return int(sz)

    def trend_analyze(self, c_length=10):
        '''
        第一步： 判断趋势
            10根K线连续处于均线以下
        '''
        self.df = self._get_market_data(self.instId, self.bar2, [self.ma])
        up_count = 0
        down_count = 0
        for index, row in self.df.iterrows():
            # 多头判断
            if not row[self.ma]:
                continue
            if float(row['low']) > float(row[self.ma]) and row[self.ma]:
                up_count += 1
            else:
                up_count = 0

            if up_count >= c_length:
                # 多头趋势
                self.df.loc[index, 'signal_long'] = row['low']
                self.df.loc[index, 'signal_flag'] = 'long'
                # return 'bull'
            # 空头判断
            if float(row['high']) < float(row[self.ma]) and row[self.ma]:
                down_count += 1
            else:
                down_count = 0

            if down_count >= c_length:
                # 空头趋势
                self.df.loc[index, 'signal_short'] = row['high']
                self.df.loc[index, 'signal_flag'] = 'short'
                # return 'fall'
        # df.to_csv("test_MA_data.csv")

    def set_signal_1h(self):
        # 判断趋势
        try:
            data = self.df.iloc[-1, :]
            if data['signal_flag'] == 'long':
                trend_signal = 'long'
            elif data['signal_flag'] == 'short':
                trend_signal = 'short'
            else:
                trend_signal = False
            return trend_signal
        except Exception as e:
            # self.log.error('MA error......%s' % e)
            return False

    def get_long_signal_3min_confirm(self):
        """
        开多条件：
            1 下引线 大于实体
            2 vol是前K线的2倍
        """

        # df_3mins = self.get_3_min_data()
        # df_3mins = self.get_3min_data_history()
        df_3mins = self._get_market_data(self.instId, self.bar1, vol_ma=20, limit='100')
        before_volume = df_3mins.iloc[-2, :]['volume']
        row2 = df_3mins.iloc[-1, :]
        bar1_close = float(row2['close'])
        self.last_price = float(row2['close'])
        _volume = float(row2['volume'])
        _open = float(row2['open'])
        _low = float(row2['low'])
        entity = abs(bar1_close - _open)
        down_wick = min(bar1_close, _open) - _low
        vol_ma = float(row2['vol_ma'])
        # 引线, 成交量，价格
        if down_wick > 0.666 * entity:
            if _volume > 2 * float(before_volume):
                if _volume >= 2 * vol_ma:
                    code, bar2_ma = self.check_price_to_ma_pec(bar1_close)
                    if code:
                        # 满足条件
                        self.signal_info_dict['price'] = bar1_close
                        self.signal_recorder['signal3'] = {'bar1': self.bar1, 'high': float(row2['high']),
                                                           'open': _open, 'low': _low, 'close': bar1_close,
                                                           'volume': _volume, "vol_ma20": vol_ma,
                                                           "before_volume": before_volume, "bar2_ma": bar2_ma,
                                                           "side": "buy", "posSide": "long"}
                        self.record_price(df_3mins)
                        return {"side": "buy", "posSide": "long"}
        return False

    def get_short_signal_3min_confirm(self):
        """
        开空条件：
            1 上引线 大于实体
            2 vol是前K线的2倍
        """
        df_3mins = self._get_market_data(self.instId, self.bar1, vol_ma=20, limit='100')
        before_volume = df_3mins.iloc[-2, :]['volume']
        row2 = df_3mins.iloc[-1, :]
        bar1_close = float(row2['close'])
        self.last_price = float(row2['close'])
        _volume = float(row2['volume'])
        _open = float(row2['open'])
        _high = float(row2['high'])
        entity = abs(bar1_close - _open)
        up_wick = _high - max(bar1_close, _open)
        vol_ma = float(row2['vol_ma'])
        # 引线, 成交量，价格
        if up_wick >= 0.666 * entity:
            if _volume >= 2 * float(before_volume):
                if _volume >= 2 * vol_ma:
                    code, bar2_ma = self.check_price_to_ma_pec(bar1_close)
                    if code:
                        # 满足条件
                        self.record_price(df_3mins)
                        self.signal_recorder['signal3'] = {'bar1': self.bar1, 'high': _high, 'open': _open,
                                                           'low': float(row2['low']), 'close': bar1_close,
                                                           'volume': _volume, "vol_ma20": vol_ma,
                                                           "before_volume": before_volume, "bar2_ma": bar2_ma,
                                                           "side": "sell", "posSide": "short"}
                        return {"side": "sell", "posSide": "short"}
        return False

    def record_price(self, df):
        try:
            pd.set_option("display.max_columns", None)
            pd.set_option('display.width', 100)
            self.log.info('信号出现， 准备开仓')
            self.log.info(df.tail(2))
            # print('信号出现， 准备开仓')
            # print(df.tail(2))
        except Exception as e:
            pass

    '''
    def stop_order(self):
        """
        实时价格突破60MA. 且超过1个ATR值，平仓止盈
         """
        ma = int(re.findall(r"\d+", self.ma)[0])
        while True:
            time.sleep(1)
            self.log.info('等待止盈信号')
            print('等待止盈信号')
            self.df = self._get_candle_data(self.instId, self.bar2)
            self.df[self.ma] = self.df['close'].rolling(ma).mean()

            check_flag = self.check_price_to_ma(self.df)
            if check_flag:
                self.close_positions_all()
                self.has_order = False
                self.stop_loss = 0
                return self.has_order
            self.has_order = self.get_positions()
            if not self.has_order:
                # 已经触发了止损
                self.log.info('止损.......')
                print('止损.......')
                self.has_order = False
                self.stop_loss += 1
                return self.has_order
    '''

    def stop_order(self, profit):
        self.log.info('等待止盈信号')
        print('等待止盈信号')
        i = 0
        try:
            if profit:
                while True:
                    time.sleep(30)
                    self.track_trading_status(update_status=False)
                    result = self.tradeAPI.get_orders_history('SWAP', limit='1')
                    order_data = result.get('data')[0]
                    para = {"long": "sell", "short": "buy"}
                    if para.get(order_data.get('posSide')) == order_data.get('side'):
                        # 平仓单
                        self.has_order = self.get_positions()
                        if self.has_order:
                            self.log.error('止损止盈检查错误， 订单ID%s' % order_data.get('ordId'))
                        try:
                            self.stop_order_all()
                        except Exception as e:
                            self.log.error(e)
                        pnl = order_data.get('pnl')
                        if float(pnl) >= 0:
                            self.track_trading_status(7)
                            print('止盈')
                            self.log.info('止盈')
                            self.stop_loss = 0
                            return self.has_order, 1
                        else:
                            self.track_trading_status(8)
                            print('亏损')
                            self.log.info('亏损')
                            self.stop_loss += 1
                            if self.stop_loss < self.max_stop_loss:
                                bar1_num = int(re.findall(r"\d+", self.bar1)[0])
                                print('止损啦！本人需要冷静片刻。。。')
                                self.log.info('止损， 休息%s在继续运行' % self.bar1)
                                time.sleep(bar1_num*60)
                        return self.has_order, 0

            else:
                ma = int(re.findall(r"\d+", self.ma)[0])
                # 实时价格突破60MA. 且超过1个ATR值，平仓止盈
                while True:
                    time.sleep(1)
                    # self.log.info('等待止盈信号')
                    self.df = self._get_candle_data(self.instId, self.bar2)
                    self.df[self.ma] = self.df['close'].rolling(ma).mean()
                    check_flag = self.check_price_to_ma(self.df)
                    if check_flag:
                        self.close_positions_all()
                        self.track_trading_status(0)
                        self.has_order = False
                        self.stop_loss = 0
                        return self.has_order, 1

                    self.has_order = self.get_positions()
                    if not self.has_order:
                        # 已经触发了止损
                        self.track_trading_status(0)
                        self.log.info('止损.......')
                        print('止损.......')
                        self.has_order = False
                        self.stop_loss += 1
                        return self.has_order, 0
        except Exception as e:
            self.log.error(e)

    def check_price_to_ma(self, df):
        # 实时价格突破60MA
        row = df.iloc[-1, :]
        ma = float(row[self.ma])
        high = float(row['high'])
        low = float(row['low'])
        # last = row['close']
        if high >= ma and low <= ma:
            atr = self.get_atr_data(df, 20)
            if self.side == 'buy':
                if ma - low >= atr:
                    return True
            else:
                if high - ma >= atr:
                    return True
        return False

    def check_price_to_ma_pec(self, bar1_close):
        # 实时价格是否接近均线百分比附近
        df = self._get_candle_data(self.instId, self.bar2, [self.ma])
        row = df.iloc[-1, :]
        # self.log.info(row)
        ma = float(row[self.ma])
        # high = float(row['high'])
        # low = float(row['low'])
        last_p = float(row['close'])
        code = self.price_to_ma(bar1_close, ma, self.ma_percent)
        # if code:
        #     print('价格在均线附近，准备开仓')
        #     self.log.info('价格在均线附近，准备开仓')
        # else:
        #     print('价格远离均线，信号无效，重新检测中')
        #     self.log.info('价格远离均线，信号无效，重新检测中')
        return code, ma

    def ready_order(self):
        # isolated cross保证金模式.全仓, market：市价单  limit：限价单 post_only：只做maker单
        # sz 委托数量
        atr = self.get_atr_data(self.df, 20)
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
            sz = self.set_my_position(accountinfo['balance'], atr)
            if sz == 0:
                msg = '仓位太小， 无法开仓 ---> *** 余额%sU ***' % accountinfo['balance']
                self.log.error(accountinfo['name'])
                self.log.error(msg)
                accountinfo['msg'] = msg
            para['sz'] = sz
            orderinfo_dict.update(para)
            result = obj_api.tradeAPI.place_order(**para)
            # result = self.tradeAPI.place_order(**para)
            ordId, sCode, sMsg= self.check_order_result_data(result, 'ordId')
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

                avgpx = self.last_price
                if self.order_lst:
                    avgpx = "%.2f" % float(self.order_lst[0].get('avgPx'))
                    orderinfo_dict['order_ctime'] = self.timestamp_to_date(self.order_lst[0].get('cTime'))
                    orderinfo_dict['order_utime'] = self.timestamp_to_date(self.order_lst[0].get('uTime'))

                orderinfo_dict['ordId'] = ordId
                orderinfo_dict['avgPx'] = avgpx

                # 设置止损止盈
                algo_para = self.set_place_algo_order_oco(obj_api, atr, sz, avgpx)
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
            if not self.matrade_open_order:
                self.send_msg_to_me()
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
        p = self.get_algo_p(atr)     # 止损点数
        self.signal_info_dict['posSide'] = self.posSide
        self.signal_info_dict['instId'] = self.instId
        self.signal_info_dict['side'] = self.side
        self.signal_info_dict['atr'] = atr
        self.signal_info_dict['p'] = p
        self.set_strategy_info(self.signal_info_dict)

        # 保存委托订单信息
        for item in placc_algo_order_info_list:
            new_dict = {}
            for i, j in item.items():
                # 把key转小写
                new_dict[i.lower()] = j
            algo = PlaceAlgo(**new_dict, strategyid=self.strategy_obj.id)
            algo.save()

    def set_strategy_info(self, data):
        signalinfo = self.strategy_obj.signalinfo
        if signalinfo:
            try:
                signalinfo = json.loads(signalinfo)
            except Exception as e:
                self.log.info(e)
                # self.log.info(signalinfo)
            if isinstance(signalinfo, list):
                signalinfo.append(data)
            else:
                signalinfo = [data]
        else:
            signalinfo = [data]
        self.strategy_obj.signalinfo = signalinfo
        self.strategy_obj.save()

    def get_3_min_data(self):
        result = self.marketAPI.get_history_candlesticks(self.instId, limit="2")
        data_lst = result.get("data")
        columns_lst = ['time', 'open', 'high', 'low', 'close', 'volume', 'volCcy']
        self.df_3mins = pd.DataFrame(data_lst, columns=columns_lst)
        return self.df_3mins

    def get_3min_data_history(self):
        file_path = '../history_data/history_3m.csv'
        df = pd.read_csv(file_path, sep=',', parse_dates=['time'])
        df.set_index(['time'], inplace=True)

    def price_to_ma(self, p, ma, ma_percent=0.01):
        # 2 判断价格接近均线 %1 附近，
        pre = abs(float(p) - float(ma)) / float(ma)
        if pre <= ma_percent:
            return True
        return False

    def set_place_algo_order_price(self, atr, avgPx, posSide):
        """ 设置止损止盈价格
            -1是市价止盈止损

            止损（ %5 * 账户资金 ） 除以 （ 3 * 建仓单位）
        """
        # p = (0.05 * self.mybalance) / (3 * self.sz / 10)
        p = self.get_algo_p(atr)
        if self.set_profit:
            if posSide == 'long':
                tp = float(avgPx) + int(self.set_profit) * p
                sl = float(avgPx) - p
            else:
                tp = float(avgPx) - int(self.set_profit) * p
                sl = float(avgPx) + p
        else:
            if posSide == 'long':
                tp = float(avgPx) * 2
                sl = float(avgPx) - p
            else:
                tp = float(avgPx) / 2
                sl = float(avgPx) + p
        # -1 为市价平仓
        p2 = "-1"
        price_para = {
            "tpTriggerPx": "%0.2f" % tp,
            "tpOrdPx": p2,
            "slTriggerPx": "%0.2f" % sl,
            "slOrdPx": p2
        }
        return price_para

    def set_place_algo_order_oco(self, obj_api, atr, sz, avgpx):
        """策略委托下单
        ordType:
            conditional：单向止盈止损
            oco：双向止盈止损
            trigger：计划委托
            move_order_stop：移动止盈止损
            iceberg：冰山委托
            twap：时间加权委托

        tpTriggerPx 止盈触发价，如果填写此参数，必须填写 止盈委托价
        tpOrdPx 止盈委托价，如果填写此参数，必须填写 止盈触发价, 委托价格为-1时，执行市价止盈
        slTriggerPx 止损触发价
        slOrdPx 止损委托价
        tpTriggerPxType = 'last' 最新价格
        """
        side = {"long": "sell", "short": "buy"}.get(self.posSide)

        price_para = self.set_place_algo_order_price(atr, avgpx, self.posSide)

        try:
            # result = self.tradeAPI.place_algo_order(self.instId, self.tdMode, self.side, ordType=self.ordType,
            #                                         sz=self.sz, posSide=self.posSide, tpTriggerPx=tpTriggerPx, tpOrdPx=tpOrdPx,
            #                                         slTriggerPx=slTriggerPx, slOrdPx=slOrdPx,
            #                                         tpTriggerPxType='last', slTriggerPxType='last')

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
            # 事件执行失败时的msg
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

    def check_signal1(self):
        # 1 首先判断是否处于趋势之中
        self.track_trading_status(update_status=False)
        self.trend_analyze()
        signal1 = self.set_signal_1h()
        if self.matrade_open_order:
            signal1 = self.matrade_open_order
        return signal1

    def check_signal2(self):
        self.log.info('正在判断信号2....................')
        print('正在判断信号2....................')

        while True:
            self.track_trading_status(update_status=False)
            time.sleep(5)
            # 获取现在的价格
            self.df = self._get_candle_data(self.instId, self.bar2, [self.ma])
            # 2 判断价格接近均线 %1 附近，
            row = self.df.iloc[-1, :]
            ma = row[self.ma]
            last_p = row['close']
            # 2 判断价格接近均线 %1 附近，
            signal2 = self.price_to_ma(last_p, ma, self.ma_percent)
            if self.matrade_open_order:
                signal2 = True
            if signal2:
                self.signal_recorder["signal2"] = {'bar2': self.bar2, 'last': last_p, 'ma': ma,
                                                   'ma_percent': self.ma_percent}

                return True

    def check_signal3(self, signal1):
        """
            检测3分钟信号
            如果3个大周期还未出现信号，则不再判断 退出程序
        """
        t_num = self.get_time_inv(self.bar2, self.big_bar_time)
        self.log.info("开始循环检测信号3")
        print("开始循环检测信号3")
        for t in range(t_num):
            self.track_trading_status(update_status=False)
            if signal1 == 'long':
                # 开多信号
                signal_order_para = self.get_long_signal_3min_confirm()
            elif signal1 == 'short':
                # 开空信号
                signal_order_para = self.get_short_signal_3min_confirm()
            else:
                signal_order_para = False
            if self.matrade_open_order:
                signal_order_para = {"side": "sell", "posSide": "short"} if self.matrade_open_order == 'short' else \
                    {"side": "buy", "posSide": "long"}
            if signal_order_para:
                self.log.info("信号3已确认！")
                self.log.info(self.signal_recorder.get('signal3'))
                return signal_order_para
            time.sleep(2)

        # 没出现信号
        self.log.info('未出现开仓信号， 停止交易')
        # print('未出现开仓信号 ，重新开始新一轮检测')
        self.track_trading_status(0)
        return 'no singnal'
        # raise Exception('未出现开仓信号， 停止交易')

    def get_time_inv(self, t, big_bar_time):
        t_num = int(re.findall(r"\d+", t)[0])
        if 'H' in t:
            t_num = t_num * 60 * 60
        elif 'm' in t:
            t_num = t_num * 60
        elif 'D' in t:
            t_num = t_num * 60 * 60 * 24
        else:
            pass
        return t_num * big_bar_time

    def set_args(self, bar):
        from ..conf import ma_trade_args
        from importlib import reload
        reload(ma_trade_args)
        try:
            data_dict = ma_trade_args.args_dict.get(bar, None)
        except Exception as e:
            self.log.error(e)
            raise
        self.log.info(data_dict)
        if data_dict is None:
            self.track_trading_status(0)
            self.log.error('大周期错误')
            raise Exception('大周期错误')
        ma_percent = data_dict.get('ma_percent')
        bar1 = data_dict.get('bar1')
        max_stop_loss = data_dict.get('stop_loss')
        set_profit = data_dict.get('set_profit')
        risk_control = data_dict.get('risk_control')
        return ma_percent, bar1, max_stop_loss, set_profit, risk_control

    def track_trading_status(self, status=0, update_status=True):
        strategy_obj = Strategy.objects.get(pk=self.strategy_obj.id)
        if strategy_obj.status == -2:
            self.log.info('已强行停止策略')
            raise Exception('已强行停止策略')
        # if self.accountinfo_obj.status == -2:
        #     raise Exception('已强行停止策略')
        if update_status:
            self.strategy_obj.status = status
            self.strategy_obj.save()
            self.log.info('更新运行状态--%s--' % status)

    def get_algo_p(self, atr):
        # 计算止损点位
        p = (0.05 * atr) / (3 * self.risk_control)
        return p

    def stop_order_all(self):
        para = {"long": "sell", "short": "buy"}
        acc_count = len(self.all_accountinfo_data_list)
        index_lst = []  # 记录已平仓ID
        i = 0
        while True:
            time.sleep(2)
            # 循环检测所有账户，手动平仓的可能耗时久
            if i == acc_count:
                i = 0
            if i in index_lst:
                i += 1
                continue
            accountinfo = self.all_accountinfo_data_list[i]
            result = accountinfo['obj_api'].tradeAPI.get_orders_history('SWAP', limit='1')
            order_data = result.get('data')[0]
            if para.get(order_data.get('posSide')) == order_data.get('side'):
                # 平仓单
                has_order = self.get_positions()
                if has_order:
                    self.log.error('止损止盈检查错误， 订单ID%s' % order_data.get('ordId'))
                # obj = accountinfo['obj']
                # obj.status = 0
                # obj.save()
                orderinfo_obj = accountinfo['orderinfo_obj']
                pnl = order_data.get('pnl')
                orderinfo_obj.pnl = pnl
                orderinfo_obj.closeavgpx = "%.2f" % float(order_data.get('avgPx'))
                orderinfo_obj.closeordid = order_data.get('ordId')
                orderinfo_obj.close_position = 1
                orderinfo_obj.save()
                index_lst.append(i)
            i += 1
            if len(index_lst) == acc_count:
                break


if __name__ == '__main__':
    ma = "MA10"
    my_ma_trade = MaTrade(ma)
    my_ma_trade.start_my_trade()


