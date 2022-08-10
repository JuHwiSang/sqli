from typing import Callable
from requests import Response
from ..dbtype import DBType

type_check_command = {
    DBType.Oracle: "(select banner from v$version where {delay_command})",
    DBType.MySQL: '@@version and {delay_command}',
    DBType.PostgreSQL: 'version() and {delay_command}'
}

class GetType:
    ex_request: Callable[[str], Response]
    is_exed: Callable[[Response], bool]
    def __init__(self, ex_request, is_exed) -> None:
        self.ex_request = ex_request
        self.is_exed = is_exed
    def run(self):
        for type, command in type_check_command.items():
            try_response = self.ex_request(command)
            if self.is_exed(try_response):
                return type
        return DBType.other