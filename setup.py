# Bootstrap installation of Distribute
import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages
from gitbot.version import __version__

PROJECT = 'gitbot'
try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(name=PROJECT,
      version=__version__,
      description='A command line tool that facilitates working with the gitbot service.',
      long_description = long_description,
      author='Lakshmi Vyas',
      author_email='lakshmi.vyas@gmail.com',
      url='http://gitbot.io/tools',
      packages=find_packages(),
      install_requires=(
          'commando',
          'fswrap',
          'pyyaml',
          'jinja2',
          'pyparsing',
          'boto'
      ),
      tests_require=(
        'nose',
      ),
      test_suite='nose.collector',
      include_package_data = True,
      entry_points={
          'console_scripts': [
              'gitbot = gitbot.main:main'
          ]
      },
      license='MIT',
      classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: MIT License',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Unix',
            'Operating System :: POSIX',
            'Operating System :: Microsoft :: Windows',
            'Programming Language :: Python',
            'Topic :: Software Development',
            'Topic :: Software Development :: Build Tools'
      ],
      zip_safe=True,
)