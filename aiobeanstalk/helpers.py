import io
import re
import yaml
from aiobeanstalk.exceptions import _BS_ERRORS, BadFormatException

# default value on server
MAX_JOB_SIZE = (2**16) - 1


def check_error(error_name):
    """Note, this will throw an error internally for every case that is a
    response that is NOT an error response, and that error will be caught,
    and checkError will return happily.

    In the case that an error was returned by beanstalkd, an appropriate error
    will be raised"""

    exeption = _BS_ERRORS.get(error_name, None)
    if not exeption:
        return
    raise exeption


_namematch = re.compile(r'^[a-zA-Z0-9+\(\);.$][a-zA-Z0-9+\(\);.$-]{0,199}$')


def check_name(name):
    """used to check the validity of a tube name"""
    if not _namematch.match(name):
        raise BadFormatException('Illegal name')


def int_it(val):
    try:
        return int(val)
    except ValueError:
        return val


def yaml_parser(yaml_string):
    """
    :param yaml_string:
    :return:
    """
    handler = io.StringIO(yaml_string)
    return yaml.load(handler)
