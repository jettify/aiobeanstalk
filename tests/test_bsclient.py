import asyncio
import unittest
import unittest.mock
import aiobeanstalk


def beanstalk_test(function):
    """Helper function base on redis_test from [0]
    https://github.com/jonathanslenders/asyncio-redis/blob/master/tests.py#L53
    """
    function = asyncio.coroutine(function)

    def wrapper(self):
        @asyncio.coroutine
        def c():
            # Create connection
            bs = yield from aiobeanstalk.connect()
            yield from function(self, bs)
        self.loop.run_until_complete(c())
    return wrapper


class BeanstalkProtocolTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(None)
        self.loop = asyncio.get_event_loop()


    def tearDown(self):
        self.loop.close()

    @beanstalk_test
    def test_basics(self, bs):
        """Test put-reserve-delete cycle"""
        tube = 'xxxtest'

        use = yield from bs.use(tube)
        self.assertEqual(use['state'], "ok")

        # # put the job on the queue
        put = yield from bs.put('test_data', 0, 0, 100)
        self.assertIsInstance(put['jid'], int)

        # watch the tube
        watch = yield from bs.watch(tube)
        self.assertEqual(watch['state'], "ok")
        self.assertIsInstance(watch['count'], int)

        # dequeue job from tube
        reserve = yield from bs.reserve()
        self.assertEqual(reserve['jid'], put['jid'])
        self.assertEqual(reserve['state'], "ok")

        # remove job from tube
        delete = yield from bs.delete(reserve['jid'])
        self.assertEqual('ok', delete['state'])


