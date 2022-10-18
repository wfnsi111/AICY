"""
连接主机：rm-j6c8n6xgpm006ks2lbo.mysql.rds.aliyuncs.com

pro只读：数据库：cy_prd 账号：lgh_pro_read 密码：Lgh_123123

pro： 数据库：lgh_pro 账号：lgh_pro 密码：Lgh_123123

test测试：数据库：lgh_test 账号：lgh_test 密码：Lgh_123123
"""
# import pymysql
#
#
# class BaseDb(object):
#     def __init__(self):
#         print('创建DB')
#         self.db = DbConncet()
#
#     def insert(self, sql):
#         self.db.cursor.execute(sql)
#
#
# class DbConncet(object):
#     __instance = None
#
#     def __new__(cls, *args, **kwargs):
#         if not cls.__instance:
#             cls.__instance = object.__new__(cls)
#         return cls.__instance
#
#     def __init__(self):
#         try:
#             print('创建DB111')
#             host = 'rm-j6cnmk10t8b7te19j3o.mysql.rds.aliyuncs.com'
#             user = 'cy_test'
#             passwd = 'Cy123456'
#             db = 'cy_test'
#             port = 3306
#             self.conn = pymysql.connect(host=host, user=user, passwd=passwd, db=db, port=port, charset='utf8')
#         except pymysql.Error as e:
#             errormsg = 'Cannot connect to server\nERROR(%s):%s' % (e.args[0], e.args[1])
#             print(errormsg)
#             exit(2)
#         self.cursor = self.conn.cursor()
#
