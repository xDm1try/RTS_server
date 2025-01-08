"""
MicroPyServer is a simple HTTP server for MicroPython projects.

@see https://github.com/troublegum/micropyserver

The MIT License

Copyright (c) 2019 troublegum. https://github.com/troublegum/micropyserver

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import asyncio
import gc
import re
import socket
import sys
import io
import uselect


class MicroPyServer(object):

    def __init__(self):

        self._routes = []
        self._connect = None
        self._on_request_handler = None
        self._on_not_found_handler = None
        self._on_error_handler = None
        self._sock = None

    async def start(self, host, port):
        if host is None or port is None:
            return
        port = int(port)
        print(f"Server checks requests on {host}:{port}")

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((host, port))
        self._sock.listen(2)
        self._sock.settimeout(3000)  # Устанавливаем некоблокирующий режим
        self._poller = uselect.poll()
        self._poller.register(self._sock, uselect.POLLIN)
        events = self._poller.poll(3000)
        for sock, event in events:
            if event & uselect.POLLIN:
                try:
                    self._connect, address = self._sock.accept()
                    self._connect.settimeout(3000)

                    request = self.get_request()
                    print(f"{request=}")
                    if request is None:
                        continue
                    if len(request) == 0:
                        self._connect.close()
                        return

                    if self._on_request_handler:
                        if not self._on_request_handler(request, address):
                            return

                    route = self.find_route(request)
                    print(f"{route=}")
                    if route:
                        route["handler"](request)
                    else:
                        self._route_not_found(request)

                except Exception as e:
                    self._internal_error(e)
                finally:
                    if self._connect:
                        self._connect.close()
        self._sock.close()

    def stop(self):
        """ Stop the server """
        self._connect.close()
        self._sock.close()
        self._sock = None
        print("Server stop")

    def add_route(self, path, handler, method="GET"):
        """ Add new route  """
        self._routes.append(
            {"path": path, "handler": handler, "method": method})

    def send(self, data):
        """ Send data to client """
        if self._connect is None:
            raise Exception("Can't send response, no connection instance")
        self._connect.sendall(data.encode())

    def find_route(self, request):
        """ Find route """
        lines = request.split("\r\n")
        method = re.search("^([A-Z]+)", lines[0]).group(1)
        path = re.search("^[A-Z]+\\s+(/[-a-zA-Z0-9_.]*)", lines[0]).group(1)
        for route in self._routes:
            if method != route["method"]:
                continue
            if path == route["path"]:
                return route
            else:
                match = re.search("^" + route["path"] + "$", path)
                if match:
                    print(method, path, route["path"])
                    return route

    def get_request(self, buffer_length=500):
        """ Return request body """
        try:
            data = self._connect.recv(buffer_length)
            data_str = str(data, "utf8")
            return data_str
        except OSError as e:
            if e.errno == 11:  # EAGAIN
                return None
            else:
                print(f"Ошибка сокета: {e}")
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    def on_request(self, handler):
        """ Set request handler """
        self._on_request_handler = handler

    def on_not_found(self, handler):
        """ Set not found handler """
        self._on_not_found_handler = handler

    def on_error(self, handler):
        """ Set error handler """
        self._on_error_handler = handler

    def _route_not_found(self, request):
        """ Route not found handler """
        if self._on_not_found_handler:
            self._on_not_found_handler(request)
        else:
            """ Default not found handler """
            self.send("HTTP/1.0 404 Not Found\r\n")
            self.send("Content-Type: text/plain\r\n\r\n")
            self.send("Not found")

    def _internal_error(self, error):
        """ Internal error handler """
        if self._on_error_handler:
            self._on_error_handler(error)
        else:
            """ Default internal error handler """
            if "print_exception" in dir(sys):
                output = io.StringIO()
                sys.print_exception(error, output)
                str_error = output.getvalue()
                output.close()
            else:
                str_error = str(error)
            self.send("HTTP/1.0 500 Internal Server Error\r\n")
            self.send("Content-Type: text/plain\r\n\r\n")
            self.send("Error: " + str_error)
            print(str_error)
