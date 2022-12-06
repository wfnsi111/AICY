# -*- coding: utf-8 -*-

from .mylog import LoggerHandler
from ..okx import Account_api as Account
from ..okx import Trade_api as Trade
from ..okx import Market_api as Market
from ..okx.AccountAndTradeApi import AccountAndTradeApi
from ...models import OrderInfo, AccountInfo, Trader
from ..weixin_msg.work import WeixinSMS
from ..conf.pieces_of_coin import pieces_of_coin
from ..conf.robot_name import robot_name
import pandas as pd
import datetime
import re
import time


class BaseTrade:
    def __init__(self, api_key, secret_key, passphrase, use_server_time=False, flag='1', logfile=None):
        self.marketAPI = Market.MarketAPI(api_key, secret_key, passphrase, use_server_time, flag)
        self.accountAPI = Account.AccountAPI(api_key, secret_key, passphrase, use_server_time, flag)
        self.tradeAPI = Trade.TradeAPI(api_key, secret_key, passphrase, use_server_time, flag)
        self.log = LoggerHandler(file=logfile)
        self.side = 'buy'
        self.trade_ok = False
        self.posSide = ''
        self.sz = "2"
        self.tdMode = 'cross'
        self.ordType = 'oco'
        self.order_lst = []
        self.mybalance = 0
        self.instId_detail = {}
        self.has_order = None
        self.order_times = 0
        self.orderinfo = {}

    def timestamp_to_date(self, t):
        # 13位时间戳转日期
        timestamp = float(t)/1000
        timearray = time.localtime(timestamp)
        date = time.strftime("%Y-%m-%d %H:%M:%S", timearray)
        return date

    def get_positions(self):
        try:
            result = self.accountAPI.get_positions('SWAP')
            self.order_lst = result.get('data', [])
            if len(self.order_lst) > 1:
                self.log.info('存在两笔订单')
            for item in self.order_lst:
                if item:
                    return True
            return False
        except:
            self.log.error('get_positions error')
            raise

    def check_order_result_data(self, data, flag_id=None):
        sMsg = ''
        try:
            data_list = data["data"]
        except:
            return False, False, sMsg
        for data in data_list:
            sCode = data.get("sCode", '')
            flag_id = data.get(flag_id, '')
            if sCode == "0":
                # 执行成功
                pass
            else:
                sMsg = data.get("sMsg")
                self.log.error(sMsg)
                return False, False, sMsg
            return flag_id, sCode, sMsg

    def close_positions_all(self):
        """ 市价平仓 """
        if not self.order_lst:
            self.get_positions()

        for item in self.order_lst:
            para = {
                "instId": item.get("instId"),
                'mgnMode': item.get('mgnMode'),
                "ccy": item.get('ccy'),
                "posSide": item.get('posSide'),
                'autoCxl': True
            }
            # self.posSide = {"buy": "long", "sell": "short"}.get(self.side, '')
            # 检测是否有委托 ，如果有委托， 先撤销委托，在平仓
            # self.algo = self.cancel_algo_order_(algoid)
            try:
                result = self.tradeAPI.close_positions(**para)
            except:
                self.log.error("平仓错误")
        self.has_order = False
        self.order_lst.clear()

    def _get_market_data(self, instId, bar, ma_lst=None, vol_ma=None, limit='100', set_index=True):
        """ 获取历史K线数据 """
        result = self.marketAPI.get_history_candlesticks(instId, bar=bar, limit=limit)
        data_lst = result.get("data")
        new_data_lst = []
        if len(data_lst[0]) == 8:
            columns_lst = ['date', 'open', 'high', 'low', 'close', 'vols', 'volume', 'volCcy']
        elif len(data_lst[0]) == 7:
            columns_lst = ['date', 'open', 'high', 'low', 'close', 'volume', 'volCcy']
        else:
            columns_lst = ['date', 'open', 'high', 'low', 'close', 'volume', 'volCcy', '?', '??']
        # 按时间从小到大排序
        l = int(limit)
        for i in range(l, 0, -1):
            data_ = data_lst[i - 1]
            data_[0] = self.timestamp_to_date(data_[0])
            new_data_lst.append(data_)
        df = pd.DataFrame(new_data_lst, columns=columns_lst)

        if set_index:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index(['date'], inplace=True)

        if isinstance(ma_lst, list):
            for ma in ma_lst:
                ma_num = int(re.findall(r"\d+", ma)[0])
                df[ma] = df['close'].rolling(ma_num).mean()
        if vol_ma:
            # vol_ma_num = int(re.findall(r"\d+", vol_ma)[0])
            df['vol_ma'] = df['volume'].rolling(vol_ma).mean()
        return df

    def _get_candle_data(self, instId, bar, ma_lst=None, vol_ma=None, limit='100'):
        """ 获取K线数据 """
        result = self.marketAPI.get_candlesticks(instId, bar=bar, limit=limit)
        data_lst = result.get("data")
        new_data_lst = []
        if len(data_lst[0]) == 8:
            columns_lst = ['date', 'open', 'high', 'low', 'close', 'vols', 'volume', 'volCcy']
        elif len(data_lst[0]) == 7:
            columns_lst = ['date', 'open', 'high', 'low', 'close', 'volume', 'volCcy']
        else:
            columns_lst = ['date', 'open', 'high', 'low', 'close', 'volume', 'volCcy', '?', '??']
        # 按时间从小到大排序
        l = int(limit)
        for i in range(l, 0, -1):
            data_ = data_lst[i - 1]
            data_[0] = self.timestamp_to_date(data_[0])
            new_data_lst.append(data_)

        df = pd.DataFrame(new_data_lst, columns=columns_lst)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index(['date'], inplace=True)
        if isinstance(ma_lst, list):
            for ma in ma_lst:
                ma_num = int(re.findall(r"\d+", ma)[0])
                df[ma] = df['close'].rolling(ma_num).mean()
        if vol_ma:
            # vol_ma_num = int(re.findall(r"\d+", vol_ma)[0])
            df['vol_ma'] = df['volume'].rolling(vol_ma).mean()
        return df

    def _get_ticker(self, instId):
        result = self.marketAPI.get_ticker(instId)
        instId_detail = result.get('data')[0]
        return instId_detail

    def get_algoid_data(self, ordType='oco'):
        """ 获取未完成策略委托单 """
        result = self.tradeAPI.order_algos_list(ordType, instType='SWAP')
        data = result.get('data')
        if not data:
            algoID = False
        else:
            algoID = True
            for item in data:
                algoID = item.get("algoId")
        return algoID

    def get_timestamp(self):
        now = datetime.datetime.now()
        t = now.isoformat("T", "milliseconds")
        return t + "Z"

    def get_order_details(self, instId, ordId=''):
        result = self.tradeAPI.get_orders(instId, ordId)
        self.order_details = result.get('data')[0]
        avgPx = self.order_details.get('avgPx')
        state = self.order_details.get('state')
        side = self.order_details.get('side')
        pnl = self.order_details.get('pnl')
        # state = self.order_details.get('state')
        msg = '%s 开仓成功，均价：%s, 状态：%s, 方向：%s' % (instId, avgPx, state, side)
        self.log.info(msg)
        return self.order_details

    def currency_to_sz(self, instId, currency):
        """ 币转张 """
        coefficient = pieces_of_coin.get(instId)
        sz = currency * coefficient
        return sz

    def set_initialization_account_all(self, all_accountinfo, strategy_name, instid):
        # 初始化状态， 设置倍数， 账户状态。
        all_accountinfo_obj = AccountInfo.objects.filter(pk__in=all_accountinfo)
        all_accountinfo_data_list = []
        for obj in all_accountinfo_obj:
            time.sleep(0.2)
            accountinfo_data = {}
            try:
                obj_api = AccountAndTradeApi(obj.api_key, obj.secret_key, obj.passphrase, False, obj.flag)
                obj_api.set_initialization_account(instid)
                balance = obj_api.get_my_balance('availEq')
                obj.balance = float(balance)
                if obj.init_balance == -1:
                    obj.init_balance = float(balance)
                obj.strategy_name = robot_name.get(strategy_name)
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

    def get_atr_data(self, df, limit):
        try:
            new_df = df.tail(int(limit)).copy()
            new_df['atr'] = pd.to_numeric(new_df['high']) - pd.to_numeric(new_df['low'])
            atr = new_df['atr'].mean()
            return atr * 1.5
        except:
            self.log.error('get ATR  error!!!!!!!!!!!!!!!!!!!!')

    def set_trading_orderinfo(self, accountinfo, **kwargs):
        try:
            orderinfo = OrderInfo(ordid=kwargs.get('ordId'), instid=kwargs.get('instId'), posside=kwargs.get('posSide'),
                                  side=kwargs.get('side'), avgpx=kwargs.get('avgPx'),
                                  tptriggerpx=kwargs.get('tpTriggerPx'), tpordpx=kwargs.get('tpOrdPx'),
                                  sltriggerpx=kwargs.get('slTriggerPx'), slordpx=kwargs.get('slOrdPx'),
                                  sz=kwargs.get('sz'), px=kwargs.get('px'), lever=kwargs.get('lever'),
                                  algoid=kwargs.get('algoid'), strategyid=kwargs.get('strategyid'),
                                  order_ctime=kwargs.get('order_ctime'), order_utime=kwargs.get('order_utime'),
                                  algo_ctime=kwargs.get('algo_ctime'))
            orderinfo.accountinfo_id = accountinfo.id
            orderinfo.save()
            self.log.info('订单信息保存成功')
            return orderinfo
        except Exception as e:
            self.log.error(e)
            self.log.error('订单信息保存失败')

    def send_msg_to_me(self, phonenumber):
        try:
            if len(phonenumber.strip()) != 11 or not phonenumber.isdigit():
                self.log.info('手机号错误，无法发送短信提示信息[trader:%s]' % phonenumber)
                return
            sendmsg = WeixinSMS(phonenumber)
            msg = sendmsg.send_msg_with_param()
            if msg == 'ok':
                self.log.info('成功发送短信到手机')
            else:
                self.log.info('发送短信到手机失败')
        except Exception as e:
            self.log.error(e)
