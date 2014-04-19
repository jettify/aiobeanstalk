from functools import wraps
from aiobeanstalk.exceptions import UnexpectedResponse, BSJobTooBig
from aiobeanstalk.helpers import check_name, int_it, yaml_parser, \
    MAX_JOB_SIZE


class _Response(object):
    """This is a simple object for describing the expected response to a
    command.


    :param word: ``str`` the first word sent back from the server (eg OK)
    :param args: the server replies with space separated positional arguments,
        this describes the names of those argumens
    :param has_data: ``bool`` stating whether or not to expect a data stream after
        the response line
    :param parse_func: ``function``, used to transform the data. This will be called
        just prior to returning the dict, and its result will
        be under the key 'data'
    """

    def __init__(self, word, args=None, has_data=False, parse_func=None):
        self.word = word
        self.args = args if args else []
        self.has_data = has_data
        self.parse_func = parse_func or (lambda x: x)

    def __str__(self):
        """will fail if attr name hasnt been set by subclass or program"""
        return self.__class__.__name__.lower()


class OK(_Response):
    pass


class Buried(_Response):
    pass


class TimeOut(_Response):
    pass


class Handler(object):

    def __init__(self, *responses):

        self.lookup = dict((r.word, r) for r in responses)
        self.eol = '\r\n'

    def _handler(self, response_raw):

        response, sep, data = response_raw.partition(self.eol)
        response = response.split(' ')
        response_status = response.pop(0)


        resp_parse_params = self.lookup.get(response_status, None)

        if not resp_parse_params:
            error_str = "Response was: {0} {1}".format(response_status, ' '.join(response))
        elif len(response) != len(resp_parse_params.args):
            error_str = "Response {} had wrong # args, got {} (expected {})"
        else: # all good
            error_str = ''

        if error_str:
            raise UnexpectedResponse(error_str)

        reply = dict(zip(resp_parse_params.args, map(int_it, response)))
        # reply['data'] = None
        reply['state'] = str(resp_parse_params)
        if not resp_parse_params.has_data:
            return reply

        reply['data'] = resp_parse_params.parse_func(data.rstrip(self.eol))
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
    def decortor(func):
        @wraps(func)
        def new_func(*args, **kw):
            command = func(*args, **kw)
            return command, Handler(*responses)
        return new_func
    return decortor


@_interaction(OK('INSERTED', ['jid']), Buried('BURIED', ['jid']))
def process_put(data, pri=1, delay=0, ttr=60):
    """The "put" command is for any process that wants to insert a job into the queue.
    It comprises a command line followed by the job body::
    """
    data_len = len(data)
    if data_len >= MAX_JOB_SIZE:
        msg = 'Job size is {} (max allowed is {}'.format(data_len, MAX_JOB_SIZE)
        raise BSJobTooBig(msg)
    put_line = 'put {pri} {delay} {ttr} {data_len}\r\n{data}\r\n'
    return put_line.format(**locals())


@_interaction(OK('USING', ['tube']))
def process_use(tube):
    """The "use" command is for producers. Subsequent put commands will put jobs into
    the tube specified by this command. If no use command has been issued, jobs
    will be put into the tube named "default"."""
    check_name(tube)
    return 'use {}\r\n'.format(tube)


@_interaction(OK('RESERVED', ['jid', 'bytes'], True))
def process_reserve():
    """This will return a newly-reserved job. If no job is available to be reserved,
    beanstalkd will wait to send a response until one becomes available. """
    return 'reserve\r\n'


@_interaction(OK('RESERVED', ['jid', 'bytes'], True), TimeOut('TIMED_OUT'))
def process_reserve_with_timeout(timeout=0):
    """This will return a newly-reserved job. If no job is available to be reserved,
    beanstalkd will wait to send a response until one becomes available. Once a
    job is reserved for the client, the client has limited time to run (TTR) the
    job before the job times out. When the job times out, the server will put the
    job back into the ready queue

    """
    if int(timeout) < 0:
        raise AttributeError('timeout must be greater than 0')
    return 'reserve-with-timeout {}\r\n'.format(timeout)


@_interaction(OK('DELETED'))
def process_delete(jid):
    """The delete command removes a job from the server entirely. It is normally used
    by the client when the job has successfully run to completion. A client can
    delete jobs that it has reserved, ready jobs, delayed jobs, and jobs that are
    buried."""
    return 'delete {}\r\n'.format(jid)


@_interaction(OK('RELEASED'), Buried('BURIED'))
def process_release(jid, pri=1, delay=0):
    """The release command puts a reserved job back into the ready queue (and marks
    its state as "ready") to be run by any client. It is normally used when the job
    fails because of a transitory error."""
    return 'release {jid} {pri} {delay}\r\n'.format(**locals())


@_interaction(OK('BURIED'))
def process_bury(jid, pri=1):
    """The "ignore" command is for consumers. It removes the
    watch list for the current connection."""
    return 'bury {jid} {pri}\r\n'.format(**locals())


@_interaction(OK('WATCHING', ['count']))
def process_watch(tube):
    """The "watch" command adds the named tube to the watch list for the current
    connection. A reserve command will take a job from any of the tubes in the
    watch list. For each new connection, the watch list initially consists of one
    tube, named "default"""
    check_name(tube)
    return 'watch {}\r\n'.format(tube)


@_interaction(OK('WATCHING', ['count']))
def process_ignore(tube):
    """The "ignore" command is for consumers. It removes the named tube from the
    watch list for the current connection"""
    check_name(tube)
    return 'ignore {}\r\n'.format(tube)


@_interaction(OK('FOUND', ['jid', 'bytes'], True))
def process_peek(jid=0):
    """The peek commands let the client inspect a job in the system."""
    if jid:
        return 'peek {}\r\n'.format(jid)


@_interaction(OK('FOUND', ['jid', 'bytes'], True))
def process_peek_ready():
    """Return the next ready job"""
    return 'peek-ready\r\n'


@_interaction(OK('FOUND', ['jid', 'bytes'], True))
def process_peek_delayed():
    """Return the delayed job with the shortest delay left"""
    return 'peek-delayed\r\n'


@_interaction(OK('FOUND', ['jid', 'bytes'], True))
def process_peek_buried():
    """Return the next job in the list of buried jobs."""
    return 'peek-buried\r\n'


@_interaction(OK('KICKED', ['count']))
def process_kick(bound=10):
    """The kick command applies only to the currently used tube. It moves jobs into
    the ready queue. If there are any buried jobs, it will only kick buried jobs.
    Otherwise it will kick delayed jobs."""
    return 'kick {}\r\n'.format(bound)


@_interaction(OK('TOUCHED'))
def process_touch(jid):
    """The "touch" command allows a worker to request more time to work on a job.
    This is useful for jobs that potentially take a long time, but you still want
    the benefits of a TTR pulling a job away from an unresponsive worker. A worker
    may periodically tell the server that it's still alive and processing a job
    (e.g. it may do this on DEADLINE_SOON). The command postpones the auto
    release of a reserved job until TTR seconds from when the command is issued."""
    return 'touch {}\r\n'.format(jid)


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_stats():
    """The stats command gives statistical information about the
    system as a whole."""
    return 'stats\r\n'


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_stats_job(jid):
    """The stats-job command gives statistical information about the specified
    job if it exists. The response is one of:

        "NOT_FOUND\r\n" if the job does not exist.
        "OK <bytes>\r\n<data>\r\n"

    <bytes> is the size of the following data section in bytes.
    <data> is a sequence of bytes of length <bytes> from the previous line. It
         is a YAML file with statistical information represented a dictionary.

    :param jid: ``int`` job id.
    """
    return 'stats-job {}\r\n'.format(jid)


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_stats_tube(tube):
    """The stats-tube command gives statistical information about the
    specified tube if it exists. The response is one of:

        "NOT_FOUND\r\n" if the tube does not exist.
        "OK <bytes>\r\n<data>\r\n"

    <bytes> is the size of the following data section in bytes.
    <data> is a sequence of bytes of length <bytes> from the previous line. It
     is a YAML file with statistical information represented a dictionary.

    :param tube: ``str`` is a name at most 200 bytes. Stats will be returned
        for this tube.
    """
    check_name(tube)
    return 'stats-tube {}\r\n'.format(tube)


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_list_tubes():
    """The list-tubes-watched command returns a list tubes currently being
    watched by the client. The response is:

        OK <bytes>\r\n
        <data>\r\n

    <bytes> is the size of the following data section in bytes.
    <data> is a sequence of bytes of length <bytes> from the previous line. It
    is a YAML file containing watched tube names as a list of strings.
    """
    return 'list-tubes\r\n'


@_interaction(OK('USING', ['tube']))
def process_list_tube_used():
    """The list-tube-used command returns the tube currently being used by the
    client. The response is:

        USING <tube>\r\n

    <tube> is the name of the tube being used.
    """
    return 'list-tube-used\r\n'


@_interaction(OK('OK', ['bytes'], True, yaml_parser))
def process_list_tubes_watched():
    """The list-tubes-watched command returns a list tubes currently
    being watched by the client.

        OK <bytes>\r\n
        <data>\r\n
    <bytes> is the size of the following data section in bytes.
    <data> is a sequence of bytes of length <bytes> from the previous line. It
       is a YAML file containing watched tube names as a list of strings.
    """
    return 'list-tubes-watched\r\n'
