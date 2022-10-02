import pymysql

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
