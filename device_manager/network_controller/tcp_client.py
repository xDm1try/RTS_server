import asyncio


class TcpClient:
    def __init__(self):
        pass

    async def run_tcp_handler(self, ip, port):

        # Server callback receives only 2 argumets (Stream reader and writer).
        # Use python closure for saving data to the object.
        async def tcp_request_handler(reader, writer):
            ...

        self._tcp_client_task = asyncio.start_server(self.tcp_request_handler, ip, port)

    async def set