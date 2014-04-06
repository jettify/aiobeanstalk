import asyncio
import collections
import logging

from aiobeanstalk import handlers
from aiobeanstalk.log import logger
from aiobeanstalk.exceptions import _BS_ERRORS


@asyncio.coroutine
def connect(host='localhost', port=11300, loop=None):
    """Connect to beanstalk server, and return instance of
    `BeanstalkProtocol`

    :param host: `str` beanstalkd server host
    :param port: `int` beanstalkd server port
    :param loop:  `EventLoop` current event loop
    """
    loop = loop or asyncio.get_event_loop()
    bs = BeanstalkProtocol()
    factory = lambda: bs
    yield from loop.create_connection(factory, host=host, port=port)
    return bs


class BeanstalkProtocol(asyncio.Protocol):

    def __init__(self):
        self._current = collections.deque()
        self.transport = None

    def __getattr__(self, attr):
        def caller(*args, **kw):
            return self._cmd(*getattr(handlers, 'process_%s' % attr)(*args, **kw))
        return caller

    def connection_made(self, transport):
        self.transport = transport
        logger.info('Beanstalk connection_made')

    def data_received(self, data):
        logger.debug('Beanstalk data_received {0}'.format(data))

        data = data.decode()
        token = data.split(" ", 1)[0].strip()

        future, handler = self._current.popleft()
        reply = handler(data)
        future.set_result((token, reply))

    def connection_lost(self, exc):
        logger.info('Beanstalk connection_lost')
        asyncio.get_event_loop().stop()

    def _cmd(self, command, handler=None):
        future = asyncio.Future()
        self._current.append((future, handler))
        self.transport.write(command.encode())
        return future

