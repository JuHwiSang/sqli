from requests import Response
from typing import Any, Callable
import threading

class PromiseRequest:
    request: Callable[[str], Response]
    command: str
    result: Response
    thread: threading.Thread
    def __init__(self, request, command) -> None:
        self.request = request
        self.command = command
    def start(self) -> None:
        self.thread = threading.Thread(target=self.todo, daemon=True)
        self.thread.start()
    def todo(self) -> None:
        self.result = self.request(self.command)
    def join(self) -> Response:
        self.thread.join()
        return self.result
    def __str__(self) -> str:
        return str(self.result)
    def __repr__(self) -> str:
        return repr(self.result)
    

def startall(promises: list["PromiseRequest"]) -> list[Response]:
    for promise in promises:
        promise.start()
    return [promise.join() for promise in promises]