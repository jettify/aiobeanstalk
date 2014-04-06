import unittest
from aiobeanstalk import handlers

command_meta_data = [
    [
        ('process_put', ('test_data', 0, 0, 10)),
        "put 0 0 10 %s\r\ntest_data\r\n" % (len('test_data'),),
        [
            ('INSERTED 3\r\n', {'state': 'ok','jid':3}),
            ('BURIED 3\r\n', {'state': 'buried','jid':3})
        ]
    ],
    [
        ('process_use', ('bar',)),
        'use bar\r\n',
        [
            ('USING bar\r\n', {'state':'ok', 'tube':'bar'})
        ]
    ],
    [
        ('process_reserve', ()),
        'reserve\r\n',
        [
            ('RESERVED 12 5\r\nabcde\r\n',{'state':'ok', 'bytes': 5, 'jid':12,
                'data':'abcde'})
        ]
    ],
    [
        ('process_reserve_with_timeout', (4,)),
        'reserve-with-timeout 4\r\n',
        [
            ('RESERVED 12 5\r\nabcde\r\n',{'state':'ok', 'bytes': 5, 'jid':12,
                'data':'abcde'}),
            ('TIMED_OUT\r\n', {'state':'timeout'})
        ]
    ],
    [
        ('process_delete', (12,)),
        'delete 12\r\n',
        [
            ('DELETED\r\n',{'state':'ok'})
        ]
    ],
    [
        ('process_touch', (185,)),
        'touch 185\r\n',
        [
            ('TOUCHED\r\n',{'state':'ok'})
        ]
    ],
    [
        ('process_release', (33,22,17)),
        'release 33 22 17\r\n',
        [
            ('RELEASED\r\n',{'state':'ok'}),
            ('BURIED\r\n',{'state':'buried'})
        ]
    ],
    [
        ('process_bury', (29, 21)),
        'bury 29 21\r\n',
        [
            ('BURIED\r\n',{'state':'ok'})
        ]
    ],
    [
        ('process_watch', ('supertube',)),
        'watch supertube\r\n',
        [
            ('WATCHING 5\r\n',{'state':'ok','count': 5})
        ]
    ],
    [
        ('process_ignore', ('supertube',)),
        'ignore supertube\r\n',
        [
            ('WATCHING 3\r\n', {'state':'ok', 'count':3})
            #('NOT_IGNORED',{'state':'buried'})
        ]
    ],
    [
        ('process_peek', (39,)),
        'peek 39\r\n',
        [
            ("FOUND 39 10\r\nabcdefghij\r\n", {'state':'ok', 'jid':39,
                'bytes':10, 'data':'abcdefghij'})
        ]
    ],
    [
        ('process_peek_ready', ()),
        'peek-ready\r\n',
        [
            ("FOUND 9 10\r\nabcdefghij\r\n",{'state':'ok', 'jid':9, 'bytes':10,
                'data':'abcdefghij'})
        ]
    ],
    [
        ('process_peek_delayed', ()),
        'peek-delayed\r\n',
        [
            ("FOUND 9 10\r\nabcdefghij\r\n",{'state':'ok', 'jid':9, 'bytes':10,
                'data':'abcdefghij'})
        ]
    ],
    [
        ('process_peek_buried', ()),
        'peek-buried\r\n',
        [
            ("FOUND 9 10\r\nabcdefghij\r\n",{'state':'ok', 'jid':9, 'bytes':10,
                'data':'abcdefghij'})
        ]
    ],
    [
        ('process_kick', (200,)),
        'kick 200\r\n',
        [
            ("KICKED 59\r\n",{'state':'ok', 'count':59})
        ]
    ],
    [
        ('process_stats', ()),
        'stats\r\n',
        [
            ('OK 15\r\n---\ntest: good\n\r\n', {'state':'ok', 'bytes':15,
                'data':{'test':'good'}})
        ]
    ],
    [
        ('process_stats_tube', ('barbaz',)),
        'stats-tube barbaz\r\n',
        [
            ('OK 15\r\n---\ntest: good\n\r\n',{'state':'ok', 'bytes':15,
                            'data':{'test':'good'}})

        ]
    ],
    [
        ('process_stats_job', (19,)),
        'stats-job 19\r\n',
        [
            ('OK 15\r\n---\ntest: good\n\r\n',{'state':'ok', 'bytes':15,
                'data':{'test':'good'}})

        ]
    ],
    [
        ('process_list_tubes', ()),
        'list-tubes\r\n',
        [
            ('OK 20\r\n---\n- default\n- foo\n\r\n', {'state':'ok', 'bytes':20,
                'data':['default','foo']})
        ]
    ],
    [
        ('process_list_tube_used',()),
        'list-tube-used\r\n',
        [
            ('USING bar\r\n', {'state':'ok', 'tube':'bar'})
        ]
    ],
    [
        ('process_list_tubes_watched', ()),
        'list-tubes-watched\r\n',
        [
            ('OK 20\r\n---\n- default\n- foo\n\r\n',{'state':'ok', 'bytes':20,
                'data':['default','foo']})

        ]
    ]
]


class BeanstalkProtocolTests(unittest.TestCase):

    def base_interaction(self, test_case):

        call_info, command_line, response_info = test_case
        process_fun, process_args = call_info

        func = getattr(handlers, process_fun)

        for response, resultcomp in response_info:
            line, handler = func(*process_args)
            msg_line = "Wrong cmd line for handler: {}".format(process_fun)
            self.assertEqual(line, command_line, msg_line)
            result = handler(response)
            msg_result = "Wrong cmd line for handler: {}".format(process_fun)
            self.assertEqual(result, resultcomp, msg_result)


def build_tests(test_cls, handlers):
    """Dynamically add test cases to TestCase class based on beanstalk command
    description [0]

    [0] http://stackoverflow.com/questions/1193909/pythons-unittest-and-dynamic-creation-of-test-cases
    """
    for test_case in  handlers:
        def ch(test_case):
            return lambda self: self.base_interaction(test_case)
        setattr(test_cls, "test_" + test_case[0][0], ch(test_case))

# dynamically add test cases to TestCase class based on `handlers_meta` data
build_tests(BeanstalkProtocolTests, command_meta_data)

if __name__ == '__main__':
    unittest.main()