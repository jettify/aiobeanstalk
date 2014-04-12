import asyncio
from aiobeanstalk.bsclient import BeanstalkProtocol


def main():
    bs = BeanstalkProtocol()
    loop = asyncio.get_event_loop()
    yield from asyncio.async(loop.create_connection(lambda: bs, host='localhost', port=11300))

    import ipdb; ipdb.set_trace()
    # status, data = yield from bs.status()
    # status, data = yield from bs.list_tube_used()
    # status, data = yield from bs.list_tubes_watched()
    status, data = yield from bs.stats()
    import ipdb; ipdb.set_trace()

    pass

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
# BeanstalkProtocol, 'localhost', 11300