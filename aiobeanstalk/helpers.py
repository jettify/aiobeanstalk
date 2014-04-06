import io
import re
import yaml
from aiobeanstalk.exceptions import _ERRORS, BadFormat

# default value on server
MAX_JOB_SIZE = (2**16) - 1


def check_error(error_name):
    """Note, this will throw an error internally for every case that is a
    response that is NOT an error response, and that error will be caught,
    and checkError will return happily.

    In the case that an error was returned by beanstalkd, an appropriate error
    will be raised"""

    err = _ERRORS.get(error_name, None)
    if not err:
        return
    raise err


_namematch = re.compile(r'^[a-zA-Z0-9+\(\);.$][a-zA-Z0-9+\(\);.$-]{0,199}$')


def check_name(name):
    """used to check the validity of a tube name"""
    if not _namematch.match(name):
        raise BadFormat('Illegal name')


def int_it(val):
    try:
        return int(val)
    except ValueError:
        return val


def load_yaml(yaml_string):
    handler = io.StringIO(yaml_string)
    return yaml.load(handler)
