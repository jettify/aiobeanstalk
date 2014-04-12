from distutils.core import setup

description_long = """
A client library for beanstalkd. beanstalkd is a lightweight queuing daemon
based on libevent. It is meant to be used across multiple systems, and takes
inspiration from memcache. More details on beanstalk can be found at:
http://xph.us/software/beanstalkd/
"""

setup(name='aiobeanstalk',
      version='0.0.1',
      description='A python client library for beanstalkd with asyncio.',
      long_description = description_long,
      author='Nickolai Novik',
      author_email='nickolainovik@gmail.com',
      url='https://github.com/jettify/aiobeanstalk',
      classifiers=[
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Communications',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Object Brokering',
        'Topic :: System'],
      packages=['aiobeanstalk']
)

