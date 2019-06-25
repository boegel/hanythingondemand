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
Remove stale .hod.d/* files.

@author: Ewan Higgs (Universiteit Gent)
@author: Kenneth Hoste (Universiteit Gent)
"""
import copy
import sys

from vsc.utils.generaloption import GeneralOption

import hod.cluster as hc
from hod import VERSION as HOD_VERSION
from hod.subcommands.subcommand import SubCommand
from hod.options import COMMON_HOD_CONFIG_OPTIONS, GENERAL_HOD_OPTIONS, PBS, SLURM
from hod.rmscheduler.rm_pbs import Pbs, master_hostname
from hod.rmscheduler.rm_slurm import Slurm


class CleanOptions(GeneralOption):
    """Option parser for 'clean' subcommand."""
    VERSION = HOD_VERSION

    def config_options(self):
        """Add general configuration options."""
        opts = copy.deepcopy(GENERAL_HOD_OPTIONS)
        opts.update(COMMON_HOD_CONFIG_OPTIONS)
        descr = ["Create configuration", "Configuration options for the 'list' subcommand"]

        self.log.debug("Add config option parser descr %s opts %s", descr, opts)
        self.add_group_parser(opts, descr)


class CleanSubCommand(SubCommand):
    """Implementation of HOD 'clean' subcommand."""
    CMD = 'clean'
    HELP = "Remove stale cluster info."

    def run(self, args):
        """Run 'clean' subcommand."""
        optparser = CleanOptions(go_args=args, envvar_prefix=self.envvar_prefix, usage=self.usage_txt)

        if optparser.options.rm_backend == SLURM:
            rm_class = Slurm
            rm_master = None
        elif optparser.options.rm_backend == PBS:
            rm_class = Pbs
            rm_master = master_hostname()
        else:
            sys.stderr.write("Unknown resource manager backend specified: %s", optparser.options.rm_backend)
            return 1

        try:
            rm = rm_class(optparser)
            state = rm.state()
            labels = hc.known_cluster_labels()
            info = hc.mk_cluster_info_dict(labels, state, master=rm_master)
            hc.clean_cluster_info(rm_master, info)
        except StandardError as err:
            self._log_and_raise(err)

        return 0
