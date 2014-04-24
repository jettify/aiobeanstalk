from functools import partial
import unittest
from aiobeanstalk.exceptions import BadFormatException
from aiobeanstalk.helpers import check_name, int_it


class HelpersTests(unittest.TestCase):

    def test_check_name_(self):
        # should not raise any exceptions
        check_name("xxx")

    def test_check_name_false(self):
        clb = partial(check_name, "^/_*^")
        self.assertRaises(BadFormatException, clb)

    def test_int_id_valid_int(self):
        self.assertEqual(int_it("10"), 10)

    def test_int_id_not_int(self):
        self.assertEqual(int_it("asyncio"), "asyncio")
