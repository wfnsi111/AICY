import random
from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError


class WeixinSMS:
    def __init__(self, phone_num='17780691144'):
        self.appid = 1400449769
        self.appkey = '32bbdc8cc64c91a3d4ce2ca2fc11e27d'
        self.sign = '刘康解忧'
        self.template_id = 1567394
        self.phone_num = phone_num

    def make_code(self):
        code = ''
        for i in range(6):
            code += str(random.randint(0, 9))
        return code

    def send_msg(self, msg):
        ssender = SmsSingleSender(self.appid, self.appkey)
        try:
            result = ssender.send(0, 86, self.phone_num, msg)
            print(result)
        except HTTPError as e:
            print('HTTPError', e)
        except Exception as e:
            print(e)

    def send_msg_with_param(self, msg_code=None):
        ssender = SmsSingleSender(self.appid, self.appkey)
        reqmsg = 'error'
        try:
            if msg_code:
                params = [msg_code]
            else:
                msg_code = self.make_code()
                params = [msg_code]
            result = ssender.send_with_param(86, self.phone_num, self.template_id, params,
                                             sign=self.sign, extend='', ext='')
            # {'result': 0, 'errmsg': 'OK', 'ext': '', 'sid': '3363:374251308916653805964229114',
            # 'fee': 1, 'isocode': 'CN'}
            if result.get('errmsg', '') == 'OK':
                return msg_code
        except HTTPError as e:
            print('HTTPError', e)
        except Exception as e:
            print(e)
        return False


if __name__ == '__main__':
    sendmsg = WeixinSMS()
    sendmsg.send_msg_with_param()
