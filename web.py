import requests

DEFAULT_ALLOW_REDIRECTS = False

class Link:
    url: str
    method: str
    params: dict[str, str]
    def __init__(self, url, method: str, params) -> None:
        self.url = url
        self.params = params
        self.method = method.upper()
    def __repr__(self) -> str:
        return f"Link({self.url!r}, {self.method!r}, {self.params!r})"
    def __str__(self) -> str:
        return repr(self)
    def request(self, params: dict = {}, allow_redirects: bool = DEFAULT_ALLOW_REDIRECTS) -> requests.Response:
        params = {**self.params, **params}
        if self.method == 'GET':
            res = requests.request(self.method, self.url, params=params, allow_redirects=allow_redirects)
        elif self.method == 'POST':
            res = requests.request(self.method, self.url, data=params, allow_redirects=allow_redirects)
        else:
            raise ValueError(f"invalid value: link.method must be 'GET' or 'POST' (not {self.method})")
        # print('request:', self.method, res.status_code, self.url, params, flush=True)
        return res
    def to_exploit(self, key, payload, form, delay_command, params={}) -> "ExploitLink":
        return ExploitLink(self.url, self.method, {**self.params, **params}, key, payload, form, delay_command)

class ExploitLink(Link):
    ex_key: str
    ex_payload: str
    ex_form: str
    ex_delay_command: str
    def __init__(self, url, method: str, params, ex_key, ex_payload, ex_form, ex_delay_command) -> None:
        self.ex_key = ex_key
        self.ex_payload = ex_payload
        self.ex_form = ex_form
        self.ex_delay_command = ex_delay_command
        super().__init__(url, method, params)
    def __repr__(self) -> str:
        return f"ExploitLink({self.url!r}, {self.method!r}, {self.params!r}, {self.ex_key!r}, {self.ex_payload!r}, {self.ex_form!r}, {self.ex_delay_command!r})"
    def ex_request(self, command: str) -> requests.Response:
        toexec = command.format(delay_command=self.ex_delay_command)
        return self.request(params={self.ex_key: self.ex_form.format(toexec=toexec)})



# def check_request_time(link: Link) -> tuple[requests.Response, float]: ...
