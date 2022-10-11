from . import Account_api as Account
from . import Trade_api as Trade
from . import Funding_api as Funding


class AccountAndTradeApi:
    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='0'):
        self.accountAPI = Account.AccountAPI(api_key, api_secret_key, passphrase, use_server_time, flag)
        self.tradeAPI = Trade.TradeAPI(api_key, api_secret_key, passphrase, use_server_time, flag)
        self.fundingAPI = Funding.FundingAPI(api_key, api_secret_key, passphrase, use_server_time, flag)

    def close_positions_all(self, order_lst=None):
        """ 市价平仓 """
        if order_lst:
            for item in order_lst:
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
                except Exception as e:
                    print(e)
                    return 'error'

            return 'ok'
        else:
            return 'error'

    def get_my_balance(self, balance_type=None):
        result = self.accountAPI.get_account('USDT')
        try:
            data = result.get('data')[0].get('details')[0]
            if balance_type is None:
                mybalance = data.get('eq', -1)
            else:
                mybalance = data.get(balance_type, -1)
        except Exception as e:
            mybalance = -1
            print('get my balance error')
        return "%.2f" % float(mybalance)

    def get_order_tp_and_sl_info(self):
        result = self.tradeAPI.order_algos_list('oco', instType='SWAP')
        data = result.get('data')
        for item in data:
            if not item:
                print('没有获取到委托单信息...')
                return False
            return item
        return False

    def set_initialization_account(self, instId, lever='50', mgnMode='cross'):
        """ 初始化账户 """
        try:
            result = self.accountAPI.get_position_mode('long_short_mode')
            result = self.accountAPI.set_leverage(instId=instId, lever=lever, mgnMode=mgnMode)
        except Exception as e:
            print(e)
            print('初始化账户 error')

    def check_account_funding_(self):
        result = self.fundingAPI.transfer_state(transId=1, type='')
        return result

    def get_asset_bills(self):
        result = self.fundingAPI.get_bills()
        data_list = result.get('data', [])
        return data_list
