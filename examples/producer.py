import asyncio
import aiobeanstalk


def main():
    bs = yield from aiobeanstalk.connect(host='localhost', port=11300)

    status, data = yield from bs.put('{"nice":"job"}')
    print(status, data)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()