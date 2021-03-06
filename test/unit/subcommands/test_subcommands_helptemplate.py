#!/usr/bin/env python
# #
# Copyright 2009-2016 Ghent University
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
@author: Ewan Higgs (Universiteit Gent)
"""

import os
import unittest
import pytest
from mock import patch

from hod.subcommands.helptemplate import HelpTemplateSubCommand

class TestHelpTemplateApplication(unittest.TestCase):
    def test_run(self):
        app = HelpTemplateSubCommand()
        test_environ = dict(PBS_DEFAULT='pbsmaster')
        test_environ.update(os.environ)
        with patch('os.environ', test_environ):
            with patch('hod.config.template.mklocalworkdir', return_value='localworkdir'):
                app.run([])

    def test_usage(self):
        app = HelpTemplateSubCommand()
        usage = app.usage()
        self.assertTrue(isinstance(usage, basestring))

