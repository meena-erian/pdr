import json


class datasources:
    """
    The datasources class defines a list of supported RDBMS types
     and their default configurations.
    """
    touple = (
        (0, "PostgreSQL"),
        (1, "Microsoft SQL"),
        (2, "MySQL/MariaDB"),
        (3, "SQLite"),
        (4, "FireBird")
    )
    POSTGRESQL = 0
    MSSQL = 1
    MYSQL = 2
    SQLIGHT = 3
    FIREBIRD = 4
    __list__ = [
        {
            "name": "PostgreSQL",
            "dialect": "postgresql",
            "config": {
                "dbname": "databasename",
                "user": "username",
                "password": "password",
                "host": "hostname or IP address",
                "port": 5432
            }
        },
        {
            "name": "Microsoft SQL",
            "dialect": "mssql+pymssql",
            "config": {
                "dbname": "master",
                "user": "sa",
                "password": "",
                "host": "localhost",
                "port": 1433
            }
        },
        {
            "name": "MySQL",
            "dialect": "mysql+mysqldb",
            "config": {
                "dbname": "master",
                "user": "root",
                "password": "password",
                "host": "localhost",
                "port": 3306
            }
        },
        {
            "name": "SQLite",
            "dialect": "sqlite+pysqlite",
            "config": {
                "dbfile": "path/to/database.db"
            }
        },
        {
            "name": "FireBird",
            "dialect": "firebird+kinterbasdb",
            "config": {
                "dbname": "databasename",
                "user": "SYSDBA",
                "password": "masterkey",
                "host": "localhost",
                "path": "C:/projects/databases/myproject.fdb",
                "port": 3050
            }
        },
    ]

    @classmethod
    def config(self, sourceid=-1):
        """Returns dict default configurations of an RDBMS by
        providing its id"""
        if sourceid == -1:
            return self.__list__
        return self.__list__[sourceid]["config"]

    @classmethod
    def json(self, sourceid=-1):
        """Returns json default configurations of an RDBMS by
        providing its id"""
        if sourceid == -1:
            return json.dumps(self.__list__, indent=2)
        return json.dumps(self.__list__[sourceid]["config"], indent=2)
