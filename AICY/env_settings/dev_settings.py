"""

连接主机：rm-j6cnmk10t8b7te19j3o.mysql.rds.aliyuncs.com

prd只读：数据库：cy_prd 账号：cy_prd_read 密码：Cy123456

pre和test： 数据库：cy_pre 账号：cy_pre 密码：Cy123456

test测试：数据库：cy_test 账号：cy_test 密码：Cy123456

"""

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cy_test',
        'USER': 'cy_test',
        'PASSWORD': 'Cy123456',
        'HOST': 'rm-j6cnmk10t8b7te19j3o.mysql.rds.aliyuncs.com',
        'PORT': 3306
    }
}
