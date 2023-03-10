import pymysql
import platform
#
# try:
#     pymysql.install_as_MySQLdb()
# except:
#     pymysql.version_info = (1, 4, 13, "final", 0)
#     pymysql.install_as_MySQLdb()
#
# try:
#     from .celery import celery_app
#
#     __all__ = ('celery_app',)
# except:
#     pass
try:
    plat = platform.system().lower()
    if plat == 'windows':
        pymysql.version_info = (1, 4, 13, "final", 0)
        pymysql.install_as_MySQLdb()

    else:
        try:
            pymysql.install_as_MySQLdb()
        except:
            pymysql.version_info = (1, 4, 13, "final", 0)
            pymysql.install_as_MySQLdb()

        try:
            from .celery import celery_app

            __all__ = ('celery_app',)
        except:
            pass
except Exception as e:
    print(e)

