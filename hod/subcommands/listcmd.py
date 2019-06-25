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
List the running applications.

@author: Ewan Higgs (Universiteit Gent)
@author: Kenneth Hoste (Universiteit Gent)
"""
import copy
import sys

from vsc.utils.generaloption import GeneralOption

from hod import VERSION as HOD_VERSION
from hod.options import COMMON_HOD_CONFIG_OPTIONS, GENERAL_HOD_OPTIONS, PBS, SLURM
from hod.rmscheduler.rm_pbs import Pbs
from hod.rmscheduler.rm_slurm import Slurm
from hod.subcommands.subcommand import SubCommand
import hod.cluster as hc
import hod.table as ht


class ListOptions(GeneralOption):
    """Option parser for 'list' subcommand."""
    VERSION = HOD_VERSION

    def config_options(self):
        """Add general configuration options."""
        opts = copy.deepcopy(GENERAL_HOD_OPTIONS)
        opts.update(COMMON_HOD_CONFIG_OPTIONS)
        descr = ["Create configuration", "Configuration options for the 'list' subcommand"]

        self.log.debug("Add config option parser descr %s opts %s", descr, opts)
        self.add_group_parser(opts, descr)


def format_list_rows(cluster_info):
    """Turn a list of 'ClusterInfo' objects into a list of strings."""
    ret = []
    for info in cluster_info:
        label = info.label if info.label is not None else '<no-label>'
        jobid = info.jobid
        if info.pbsjob is None:
            state, hosts = '<job-not-found>', '<none>'
        else:
            state, hosts = info.pbsjob.state, info.pbsjob.hosts
        ret.append((label, jobid, state, hosts))
    return ret


class ListSubCommand(SubCommand):
    """Implementation of HOD 'list' subcommand."""
    CMD = 'list'
    HELP = "List submitted/running clusters"

    def run(self, args):
        """Run 'list' subcommand."""
        optparser = ListOptions(go_args=args, envvar_prefix=self.envvar_prefix, usage=self.usage_txt)

        if optparser.options.rm_backend == SLURM:
            rm_class = Slurm
        elif optparser.options.rm_backend == PBS:
            rm_class = Pbs
        else:
            sys.stderr.write("Unknown resource manager backend specified: %s", optparser.options.rm_backend)
            return 1

        try:
            rm = rm_class(optparser)
            state = rm.state()
            labels = hc.known_cluster_labels()
            info = hc.mk_cluster_info_dict(labels, state)
            if not info:
                print 'No jobs found'
                sys.exit(0)

            headers = ['Cluster label', 'Job ID', 'State', 'Hosts']
            info_rows = format_list_rows(info)
            print ht.format_table(info_rows, headers)
        except StandardError as err:
            self._log_and_raise(err)

        return 0
