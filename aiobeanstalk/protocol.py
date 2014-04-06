from collections import deque
import logging
import asyncio
from aiobeanstalk import handlers

from aiobeanstalk.log import logger
from aiobeanstalk.exceptions import _ERRORS


@asyncio.coroutine
def connect(host='localhost', port=11300, loop=None):
    loop = loop or asyncio.get_event_loop()
    bs = BeanstalkProtocol()
    factory = lambda: bs
    yield from loop.create_connection(factory, host=host, port=port)
    return bs


class Command(object):

    def __init__(self, command, **kwargs):
        """
        Create a command.

        :param command: the name of the command.
        :type command: C{str}

        :param kwargs: this values will be stored as attributes of the object
        for future use
        """
        self.command = command
        self._f = asyncio.Future()
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return "<Command: %s>" % self.command

    def success(self, value):
        self._f.set_result(value)


    def fail(self, error):
        self._f.set_exception(error)


class BeanstalkProtocol(asyncio.Protocol):

    def __init__(self):
        self._current = deque()
        self.transport = None

    def __getattr__(self, attr):
        def caller(*args, **kw):
            return self._cmd(*getattr(handlers, 'process_%s' % attr)(*args, **kw))
        return caller

    def connection_made(self, transport):
        self.transport = transport
        logger.log(logging.INFO, 'Beanstalk connection_made')

    def data_received(self, data):
        logger.debug('Beanstalk data_received {0}'.format(data))

        data = data.decode()
        token = data.split(" ", 1)[0].strip()

        if token in _ERRORS:
            cmd = self._current.popleft()
            cmd.fail(_ERRORS[token]())
            return

        future, handler = self._current.pop()
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

