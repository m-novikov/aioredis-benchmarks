from collections import deque
from urllib.parse import urlparse

import asyncio
import time
import socket
import hiredis
import enum
import os

from typing import Optional
from . import bench_config


@enum.unique
class _State(enum.IntEnum):
    not_connected = enum.auto()
    connected = enum.auto()
    error = enum.auto()


class RedisProtocol(asyncio.Protocol):
    """
    Implementation of Redis protocol
    TODO: PubSub
    """

    def __init__(self):
        self._state = _State.not_connected
        self._resp_queue = deque()

        self._transport: Optional[asyncio.Transport] = None

        self._parser = hiredis.Reader()

        self._responder_task = None
        self._exc = None
        self._loop = asyncio.get_event_loop()

    def connection_made(self, transport: asyncio.Transport):
        self._transport = transport
        sock = transport.get_extra_info("socket")
        if sock is not None:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self._state = _State.connected

    def send_command(self, cmd):
        fut = self._loop.create_future()

        if self._state == _State.connected:
            # It's possible that connection was dropped and connection_callback was not
            # called yet, to stop spamming errors, avoid writing to closed connection
            # buffer all futures to communicate reason after we get the info
            if not self._transport.is_closing():
                self._transport.write(cmd)

            self._resp_queue.append(fut)

        elif self._state == _State.not_connected:
            fut.set_exception(Exception("Not connected"))

        elif self._state == _State.error:
            assert self._exc
            fut.set_exception(self._exc)

        return fut

    def data_received(self, data):
        if self._state != _State.connected:
            return

        self._parser.feed(data)
        res = self._parser.gets()

        while res is not False:
            try:
                fut = self._resp_queue.popleft()
            except IndexError:
                # Extra unexpected data received from connection
                # e.g. connected to non-redis service
                self._set_exception(Exception("extra data"))
                break

            else:
                fut.set_result(res)

            res = self._parser.gets()

    def _set_exception(self, exc):
        self._exc = exc
        self._state = _State.error

    def connection_lost(self, exc):
        if exc is not None:
            self._set_exception(exc)

        elif self._state == _State.connected:
            exc = Exception("disconnected")
            self._state = _State.not_connected

        while self._resp_queue:
            fut = self._resp_queue.popleft()
            fut.set_exception(exc)


class Conneciton:
    def __init__(self, host, port) -> None:
        self._host = host
        self._port = port

        self._proto = RedisProtocol()
        self._conn = None

    async def connect(self):
        self._conn = await asyncio.get_event_loop().create_connection(
            lambda: self._proto, self._host, self._port
        )
        return self

    def send_command(self, cmd):
        return self._proto.send_command(cmd)


class RedisWithTransports:
    def __init__(self, host, port, max_conn, username=None, password=None):
        self._host = host
        self._port = port
        self._max_conn = max_conn
        self._connection_pool = deque(maxlen=self._max_conn)
        self._username = username
        self._password = password

    async def initialize_connection_pool(self):
        for _ in range(self._max_conn):
            conn = Conneciton(self._host, self._port)
            await conn.connect()
            if self._username and self._password:
                auth_resp = await conn.send_command(
                    b"AUTH %b %b\r\n"
                    % (self._username.encode(), self._password.encode())
                )
                assert auth_resp == b"OK"
            self._connection_pool.append(conn)

    def execute_command(self, cmd):
        conn = self._connection_pool.popleft()
        self._connection_pool.append(conn)
        return conn.send_command(cmd)

    async def auth(self, user: str, password: str):
        return await self.execute_command(
            b"AUTH %b %b\r\n" % (user.encode(), password.encode())
        )

    async def get(self, key: str) -> bytes:
        return await self.execute_command(b"GET %b\r\n" % key.encode())

    async def set(self, key: str, value, ex: int) -> bytes:
        resp = await self.execute_command(
            b"SET %b %b EX %d\r\n" % (key.encode(), repr(value).encode(), ex)
        )
        return resp == b"OK"


async def task(i, redis):
    key = f"key:{i}"
    v = await redis.get(key)
    new_v = 1 if v is None else int(v.decode()) + 1
    await redis.set(key, new_v, ex=600)


async def run(n=1500):
    parsed = urlparse(bench_config.url)
    simple_client = RedisWithTransports(
        parsed.hostname,
        parsed.port,
        max_conn=bench_config.max_conn,
        username=parsed.username,
        password=parsed.password,
    )
    await simple_client.initialize_connection_pool()

    tasks = [asyncio.create_task(task(i, simple_client)) for i in range(n)]
    start = time.time()
    await asyncio.gather(*tasks)
    t = time.time() - start
    print(
        f"simple_async: {n} tasks with blocking pool with {bench_config.max_conn} connections: {t}s"
    )


if __name__ == "__main__":
    asyncio.run(run(n=bench_config.num_iterations))
