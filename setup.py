#!/usr/bin/env python
# -*- coding: latin-1 -*-
# #
# Copyright 2009-2013 Ghent University
#
# This file is part of hanythingondemand
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://vscentrum.be/nl/en),
# the Hercules foundation (http://www.herculesstichting.be/in_English)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# http://github.com/hpcugent/hanythingondemand
#
# hanythingondemand is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# hanythingondemand is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hanythingondemand. If not, see <http://www.gnu.org/licenses/>.
# #
"""
Setup for Hanything on Demand
"""
import os
import sys
import subprocess
from setuptools import setup, Command

def setup_openmp_libpath():
    libpath = os.getenv('LD_LIBRARY_PATH')
    os.environ['LD_LIBRARY_PATH'] = '/usr/lib64/openmpi/lib:%s' % libpath

class BaseCommand(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

class TestCommand(BaseCommand):
    description = "Run unit tests."

    def run(self):
        # Cheeky cheeky LD_LIBRARY_PATH hack for Fedora
        setup_openmp_libpath()
        ret = subprocess.call("python -m unittest discover -b -s test/unit -v".split(' '))
        sys.exit(ret)

class CoverageCommand(BaseCommand):
    description = "Run unit tests."

    def run(self):
        setup_openmp_libpath()
        ret = subprocess.call(["coverage", "run", "--source=hod", "-m", "unittest", "discover", "-b", "-s", "test/unit/ -v"])
        ret = subprocess.call(["coverage", "report"])
        sys.exit(ret)


PACKAGE = {
    'name': 'hanythingondemand',
    'version': '2.1.3',
    'author': ['stijn.deweirdt@ugent.be', 'jens.timmerman@ugent.be', 'ewan.higgs@ugent.be'],
    'maintainer': ['stijn.deweirdt@ugent.be', 'jens.timmerman@ugent.be', 'ewan.higgs@ugent.be'],
    'license': "GPL v2",
    'install_requires': [
        'vsc-base >= 1.7.3',
        'mpi4py',
        'pbs-python',
        'netifaces',
        'netaddr',
    ],
    'tests_require': ['tox', 'pytest', 'coverage', 'mock'],
    'packages': [
        'hod',
        'hod.work',
        'hod.commands',
        'hod.config',
        'hod.rmscheduler',
    ],
    'data_files': [
        #('config', 'etc/Hadoop-2.0.0-cdh4.4.0/hadoop.conf')
        ],
    'scripts': ['bin/hod_main.py', 'bin/hod_pbs.py'],
    'cmdclass' : {'test': TestCommand, 'cov': CoverageCommand},
    'long_description': open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
}

if __name__ == '__main__':
    setup(**PACKAGE)
