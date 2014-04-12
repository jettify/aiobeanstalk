import asyncio
import aiobeanstalk


def main():
    bs = yield from aiobeanstalk.connect(host='localhost', port=11300)
    # wait for job from *default* tube
    res_data = yield from bs.reserve()
    print(res_data)
    data = yield from bs.delete(res_data['jid'])
    print(data)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()