import asyncio
import collections

from aiobeanstalk import handlers
from aiobeanstalk.helpers import check_error
from aiobeanstalk.log import logger


@asyncio.coroutine
def connect(host='localhost', port=11300, loop=None):
    """Connect to beanstalk server, and return instance of
    `BeanstalkProtocol`

    :param host: ``str`` beanstalkd server host
    :param port: ``int`` beanstalkd server port
    :param loop:  ``EventLoop`` current event loop
    """
    loop = loop or asyncio.get_event_loop()
    bs = yield from Beanstalk.connect(host, port, loop=loop)
    logger.debug("Connection established on: {}:{}".format(host, port))
    return bs


class Beanstalk:

    def __init__(self, reader, writer):
        self.reader, self.writer = reader, writer
        self._queue = collections.deque()

    def __getattr__(self, attr):
        def caller(*args, **kw):
            h = getattr(handlers, 'process_{}'.format(attr))
            return self._cmd(*h(*args, **kw))
        return caller

    def _cmd(self, command, handler=None):
        self._queue.append(handler)
        self.writer.write(command.encode())
        return asyncio.Task(self._read_response())

    @classmethod
    @asyncio.coroutine
    def connect(cls, host, port, loop):
        reader, writer = yield from asyncio.open_connection(host, port, loop=loop)
        return cls(reader, writer)

    @asyncio.coroutine
    def _read_response(self):
        # parse the data received as server response
        status_raw = yield from self.reader.readline()
        spl = status_raw.decode('utf8').split()
        status, values = spl[0], spl[1:]

        check_error(status)

        handler = self._queue.popleft()
        if handler.lookup[status].has_data:
            size = int(values[-1])
            # read the body including the terminating two bytes of crlf
            body = yield from self.reader.readexactly(size + 2)
            reply = handler((status_raw + body).decode())
        else:
            reply = handler(status_raw.decode())
        return reply

