from . import Account_api as Account
from . import Trade_api as Trade


class AccountAndTradeApi:
    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='0'):
        self.accountAPI = Account.AccountAPI(api_key, api_secret_key, passphrase, use_server_time, flag)
        self.tradeAPI = Trade.TradeAPI(api_key, api_secret_key, passphrase, use_server_time, flag)

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
