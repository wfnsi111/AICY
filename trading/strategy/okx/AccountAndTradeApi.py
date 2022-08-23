from . import Account_api as Account
from . import Trade_api as Trade


class AccountAndTradeApi:
    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='0'):
        self.AccountAPI = Account.AccountAPI(api_key, api_secret_key, passphrase, use_server_time, flag)
        self.TradeAPI = Trade.TradeAPI(api_key, api_secret_key, passphrase, use_server_time, flag)


