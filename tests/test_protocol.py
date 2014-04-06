import asyncio
import unittest
import unittest.mock
from aiobeanstalk.protocol import BeanstalkProtocol


@asyncio.coroutine
def _connect(loop, protocol=BeanstalkProtocol):
    transport, protocol = yield from loop.create_connection(
        protocol, 'localhost', 11300)
    return transport, protocol


def beanstalk_test(function):
    """Helper function base on redis_test from [0]
    https://github.com/jonathanslenders/asyncio-redis/blob/master/tests.py#L53
    """
    function = asyncio.coroutine(function)

    def wrapper(self):
        @asyncio.coroutine
        def c():
            # Create connection
            transport, protocol = yield from _connect(self.loop, self.protocol_class)

            yield from function(self, transport, protocol)

        self.loop.run_until_complete(c())
    return wrapper


class BeanstalkProtocolTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(None)
        self.loop = asyncio.get_event_loop()
        self.protocol_class = BeanstalkProtocol


    def tearDown(self):
        self.loop.close()

    @beanstalk_test
    def test_basics(self, transport, protocol):
        """Test put-reserve-delete cycle"""
        bs = protocol
        tube = 'xxxtest'

        use_status, use_data= yield from bs.use(tube)
        self.assertEqual('USING', use_status)

        # put the job on the queue
        put_status, put_data = yield from bs.put('test_data', 0, 0, 10)
        self.assertIsInstance(put_data['jid'], int)
        self.assertEqual('INSERTED', put_status)

        # watch the tupe
        watch_status, watch_data = yield from bs.watch(tube)
        self.assertEqual('WATCHING',  watch_status)
        self.assertIsInstance(watch_data['count'], int)

        # dequeue job from tube
        res_status, res_data = yield from bs.reserve()
        self.assertEqual(res_data['jid'], put_data['jid'])
        self.assertEqual('RESERVED', res_status)

        # remove job from tube
        del_status, del_data = yield from bs.delete(res_data['jid'])
        self.assertEqual("DELETED", del_status)
