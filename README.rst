aiobeanstalk
============

**aiobeanstalk** is a library for accessing beanstalk_ message queue
from the asyncio_ (PEP-3156/tulip) framework. Basicly code ported from awesome
pybeanstalk_ project and their twisted adapter.

Library is **not stable** and there are **some tests** .

Example
=======

Producer

.. code-block:: python

    import asyncio
    import aiobeanstalk


    def main():
        bs = yield from aiobeanstalk.connect(host='localhost', port=11300)

        data = yield from bs.put('{"nice":"job"}')
        print(data)

    if __name__ == '__main__':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()


Consumer

.. code-block:: python

    import asyncio
    import aiobeanstalk


    def main():
        bs = yield from aiobeanstalk.connect(host='localhost', port=11300)
        # wait for job from *default* tube
        res_data = yield from bs.reserve()
        print(res_data)
        status, data = yield from bs.delete(res_data['jid'])
        print(data)

    if __name__ == '__main__':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()

.. _beanstalk: https://github.com/kr/beanstalkd
.. _asyncio: http://docs.python.org/3.4/library/asyncio.html
.. _pybeanstalk: https://github.com/sophacles/pybeanstalk


Other Projects
==============
I have learned a lot from this projects, authors have done great work,
give them a try first.

* https://github.com/sophacles/pybeanstalk
* https://github.com/kr/beanstalkd
* https://bitbucket.org/nephics/beanstalkt
* https://github.com/earl/beanstalkc
