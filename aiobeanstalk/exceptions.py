"""
Detailed information about beanstalk protocol:

https://github.com/kr/beanstalkd/blob/master/doc/protocol.txt
"""


class AioBeanstalkException(Exception):
    pass


class BadFormatException(AioBeanstalkException):
    """Bad name format of tube. Names may contain letters (A-Z and
    a-z), numerals (0-9), hyphen ("-"), plus ("+"), slash ("/"), semicolon (";"),
    dot ("."), dollar-sign ("$"), underscore ("_"), and parentheses ("(" and ")"),
    but they may not begin with a hyphen.
    """


class UnexpectedResponse(AioBeanstalkException):
    """Beanstald returns unexpected result, and no one knows how to
    deal with it"""


class BadFormatJobTooBig(AioBeanstalkException):
    """

    """



class BeanstalkException(AioBeanstalkException):
    """Base class for Beanstalk exception errors."""
    pass


class BSOutOfMemory(BeanstalkException):
    """Beanstalk responded "OUT_OF_MEMORY\r\n" The server cannot allocate enough
    memory for the job. The client should try again later."""

    bs_error = 'OUT_OF_MEMORY'


class BSInternalError(BeanstalkException):
    """Beanstalk responded "INTERNAL_ERROR\r\n" This indicates a bug in the
     server. It should never happen. If it does happen, please report it at
    http://groups.google.com/group/beanstalk-talk."""

    bs_error = 'INTERNAL_ERROR'


class BSBadFormat(BeanstalkException):
    """ Beanstalk responded "BAD_FORMAT\r\n" The client sent a command line that
    was not well-formed. This can happen if the line does not end with \r\n,
    if non-numeric characters occur where an integer is expected, if the
    wrong number of arguments are present, or if the command line is
    mal-formed in any other way."""

    bs_error = 'BAD_FORMAT'


class BSUnknownCommand(BeanstalkException):
    """Beanstalk responded 'UNKNOWN_COMMAND\r\n'. The client sent a command that the server does not
    know."""

    bs_error = 'UNKNOWN_COMMAND'


class BSTimedOut(BeanstalkException):
    """
    If a non-negative timeout was specified and the timeout exceeded before a job
    became available, or if the client's connection is half-closed, the server
    will respond with TIMED_OUT
    """
    bs_error = 'TIMED_OUT'


class BSNotFount(BeanstalkException):
    """Raised if the job does not exist or is not either reserved by the
    client, ready, or buried. This could happen if the job timed out before the
    client sent the delete command.
    """
    bs_error = 'NOT_FOUND'


class BSDraining(BeanstalkException):
    """This means that the server has been put into "drain mode"
    and is no longer accepting new jobs. The client should try another server
    or disconnect and try again later."""

    bs_error = 'DRAINING'


class BSExpectedCRLF(BeanstalkException):
    """The job body must be followed by a CR-LF pair, that is,
    "\r\n". These two bytes are not counted in the job size given by the client
    in the put command line."""

    bs_error = 'EXPECTED_CRLF'


class BSJobTooBig(BeanstalkException):
    """The client has requested to put a job with a body larger
    than max-job-size bytes."""

    bs_error = 'JOB_TOO_BIG'


class BSDeadlineSoon(BeanstalkException):
    """During the TTR of a reserved job, the last second is kept by the server
    as a safety margin, during which the client will not be made to wait
    for another job. If the client issues a reserve command during the safety
    margin, or if the safety margin arrives while the client is waiting on
    a reserve command,the server will respond with"""

    bs_error = 'DEADLINE_SOON'


class BSNotIgnored(BeanstalkException):
    """if the client attempts to ignore the only tube in its
    watch list."""

    bs_error = 'NOT_IGNORED'


_BS_ERRORS = {
    'TIMED_OUT': BSTimedOut,
    'NOT_FOUND': BSNotFount,
    'BAD_FORMAT': BSBadFormat,
    'INTERNAL_ERROR': BSInternalError,
    'DRAINING': BSDraining,
    'UNKNOWN_COMMAND': BSUnknownCommand,
    'OUT_OF_MEMORY': BSOutOfMemory,
    'EXPECTED_CRLF': BSExpectedCRLF,
    'JOB_TOO_BIG': BSJobTooBig,
    'DEADLINE_SOON': BSDeadlineSoon,
    'NOT_IGNORED': BSNotIgnored
}


