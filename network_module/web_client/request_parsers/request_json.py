from ujson import loads


def get_request_lines(request: str) -> list[str]:
    return list(map(lambda line: line.strip(), request.split("\r\n")))


def get_request_content_type(request: str) -> str:
    lines: list[str] = get_request_lines(request)
    for line in lines:
        if "Content-Type:" in line:
            words = line.split(" ")
            return words[1]


def split_headers_body(request: str) -> (str, str):
    return request.split("\r\n\r\n")


def get_request_json(request: str) -> dict | None:
    _ , body = split_headers_body(request)
    try:
        d = loads(body)
        return d
    except ValueError as exc:
        raise exc
