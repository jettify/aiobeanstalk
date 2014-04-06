from functools import wraps
from aiobeanstalk.exceptions import UnexpectedResponse, BSJobTooBig
from aiobeanstalk.helpers import check_error, check_name, int_it, yaml_parser, \
    MAX_JOB_SIZE


class Response(object):
    """This is a simple object for describing the expected response to a
    command. It is intended to be subclassed, and the subclasses to be named
    in such a way as to describe the response.  For example, I've used
    OK for the expected normal response, and Buried for the cases where
    a command can result in a burried job.

    Arguments/attributes:
        word: the first word sent back from the server (eg OK)
        args: the server replies with space separated positional arguments,
              this describes the names of those argumens
        has_data: boolean stating whether or not to expect a data stream after
                 the response line
        parsefunc: a function, used to transform the data. This will be called
                   just prior to returning the dict, and its result will
                   be under the key 'data'
    """

    def __init__(self, word, args=None, has_data=False, parsefunc=None):
        self.word = word
        self.args = args if args else []
        self.has_data = has_data
        self.parsefunc = parsefunc or (lambda x: x)

    def __str__(self):
        """will fail if attr name hasnt been set by subclass or program"""
        return self.__class__.__name__.lower()


class OK(Response):
    pass


class Buried(Response):
    pass


class TimeOut(Response):
    pass


class Handler(object):

    def __init__(self, *responses):

        self.lookup = dict((r.word, r) for r in responses)
        self.eol = '\r\n'

    def _handler(self, resp):

        response, sep, data = resp.partition(self.eol)
        response = response.split(' ')
        word = response.pop(0)
        check_error(word)
        resp = self.lookup.get(word, None)

        if not resp:
            error_str = "Response was: {0} {1}".format(word, ' '.join(response))
        elif len(response) != len(resp.args):
            error_str = "Response {} had wrong # args, got {} (expected {})"
        else: # all good
            error_str = ''

        if error_str:
            raise UnexpectedResponse(error_str)

        reply = dict(zip(resp.args, map(int_it, response)))
        reply['state'] = str(resp)
        if not resp.has_data:
            return reply

        reply['data'] = resp.parsefunc(data.rstrip(self.eol))
        return reply

    def __call__(self, *args, **kwargs):
        return self._handler(*args, **kwargs)


def _interaction(*responses):
    """Decorator-factory for process_* protocol functions. Takes N response
    objects as arguments, and returns decorator.

    The decorator replaces the wrapped function, and returns the result of
    the original function, as well as a response handler set up to use the
    expected responses. Copied from [0]

    [0] https://github.com/sophacles/pybeanstalk/blob/master/beanstalk/protohandler.py#L202
    """
    def deco(func):
        @wraps(func)
        def new_func(*args, **kw):
            line = func(*args, **kw)
            return line, Handler(*responses)
        return new_func
    return deco


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_stats():
    # <data> (YAML struct)
    return 'stats\r\n'


@_interaction(OK('INSERTED', ['jid']), Buried('BURIED', ['jid']))
def process_put(data, pri=1, delay=0, ttr=60):
    """ """
    data_len = len(data)
    if data_len >= MAX_JOB_SIZE:
        msg = 'Job size is {} (max allowed is {}'.format(data_len, MAX_JOB_SIZE)
        raise BSJobTooBig(msg)
    put_line = 'put {pri} {delay} {ttr} {data_len}\r\n{data}\r\n'
    return put_line.format(**locals())


@_interaction(OK('USING', ['tube']))
def process_use(tube):
    """ """
    check_name(tube)
    return 'use {}\r\n'.format(tube)


@_interaction(OK('RESERVED', ['jid', 'bytes'], True))
def process_reserve():
    """ """
    return 'reserve\r\n'


@_interaction(OK('RESERVED', ['jid', 'bytes'], True), TimeOut('TIMED_OUT'))
def process_reserve_with_timeout(timeout=0):
    """ 

    :rtype timeout: ``int``
    """
    if int(timeout) < 0:
        raise AttributeError('timeout must be greater than 0')
    return 'reserve-with-timeout {}\r\n'.format(timeout)


@_interaction(OK('DELETED'))
def process_delete(jid):
    """ """
    return 'delete {}\r\n'.format(jid)


@_interaction(OK('RELEASED'), Buried('BURIED'))
def process_release(jid, pri=1, delay=0):
    """ """
    return 'release {jid} {pri} {delay}\r\n'.format(**locals())


@_interaction(OK('BURIED'))
def process_bury(jid, pri=1):
    """ """
    return 'bury {jid} {pri}\r\n'.format(**locals())


@_interaction(OK('WATCHING', ['count']))
def process_watch(tube):
    """ """
    check_name(tube)
    return 'watch {}\r\n'.format(tube)


@_interaction(OK('WATCHING', ['count']))
def process_ignore(tube):
    """ """
    check_name(tube)
    return 'ignore {}\r\n'.format(tube)


@_interaction(OK('FOUND', ['jid', 'bytes'], True))
def process_peek(jid=0):
    """

    :type jid: object
    """
    if jid:
        return 'peek {}\r\n'.format(jid)


@_interaction(OK('FOUND', ['jid', 'bytes'], True))
def process_peek_ready():
    """ """
    return 'peek-ready\r\n'


@_interaction(OK('FOUND', ['jid', 'bytes'], True))
def process_peek_delayed():
    """ """
    return 'peek-delayed\r\n'


@_interaction(OK('FOUND', ['jid', 'bytes'], True))
def process_peek_buried():
    """ """
    return 'peek-buried\r\n'


@_interaction(OK('KICKED', ['count']))
def process_kick(bound=10):
    """ """
    return 'kick {}\r\n'.format(bound)


@_interaction(OK('TOUCHED'))
def process_touch(jid):
    """ """
    return 'touch {}\r\n'.format(jid)


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_stats():
    """ """
    return 'stats\r\n'


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_stats_job(jid):
    """ """
    return 'stats-job {}\r\n'.format(jid)


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_stats_tube(tube):
    """ """
    check_name(tube)
    return 'stats-tube {}\r\n'.format(tube)


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_list_tubes():
    """ """
    return 'list-tubes\r\n'


@_interaction(OK('USING', ['tube']))
def process_list_tube_used():
    """ """
    return 'list-tube-used\r\n'


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_list_tubes_watched():
    """ """
    return 'list-tubes-watched\r\n'
