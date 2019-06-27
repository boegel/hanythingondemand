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
Connect to a hod cluster.

@author: Ewan Higgs (Ghent University)
@author: Kenneth Hoste (Ghent University)
"""
import copy
import os
import sys

from vsc.utils.generaloption import GeneralOption

from hod import VERSION as HOD_VERSION
from hod.cluster import cluster_env_file, cluster_jobid
from hod.options import COMMON_HOD_CONFIG_OPTIONS, GENERAL_HOD_OPTIONS, PBS, SLURM
from hod.rmscheduler.rm_pbs import Pbs
from hod.rmscheduler.rm_slurm import Slurm
from hod.subcommands.subcommand import SubCommand


class ConnectOptions(GeneralOption):
    """Option parser for 'connect' subcommand."""
    VERSION = HOD_VERSION
    ALLOPTSMANDATORY = False  # let us use optionless arguments.

    def config_options(self):
        """Add general configuration options."""
        opts = copy.deepcopy(GENERAL_HOD_OPTIONS)
        opts.update(COMMON_HOD_CONFIG_OPTIONS)
        descr = ["Create configuration", "Configuration options for the 'list' subcommand"]

        self.log.debug("Add config option parser descr %s opts %s", descr, opts)
        self.add_group_parser(opts, descr)


class ConnectSubCommand(SubCommand):
    """
    Implementation of HOD 'connect' subcommand.
    Jobs must satisfy three constraints:
        1. Job must exist in the hod.d directory.
        2. The job must exist according to PBS.
        3. The job much be in running state.
    """
    CMD = 'connect'
    HELP = "Connect to a hod cluster."
    EXAMPLE = "hod connect <label>"

    def run(self, args):
        """Run 'connect' subcommand."""
        optparser = ConnectOptions(go_args=args, envvar_prefix=self.envvar_prefix, usage=self.usage_txt)

        if optparser.options.rm_backend == SLURM:
            rm_class = Slurm
        elif optparser.options.rm_backend == PBS:
            rm_class = Pbs
        else:
            sys.stderr.write("Unknown resource manager backend specified: %s", optparser.options.rm_backend)
            return 1

        try:
            if len(optparser.args) > 1:
                label = optparser.args[1]
            else:
                self.report_error("No label provided.")

            print "Connecting to HOD cluster with label '%s'..." % label

            try:
                jobid = cluster_jobid(label)
                env_script = cluster_env_file(label)
            except ValueError as err:
                self.report_error(err)

            print "Job ID found: %s" % jobid

            pbs = rm_class(optparser)
            jobs = pbs.state()
            pbsjobs = [job for job in jobs if job.jobid == jobid]

            if len(pbsjobs) == 0:
                self.report_error("Job with job ID '%s' not found by pbs.", jobid)
            elif len(pbsjobs) > 1:
                self.report_error("Multiple jobs found with job ID '%s': %s", jobid, pbsjobs)

            pbsjob = pbsjobs[0]
            if pbsjob.state == ['Q', 'H']:
                # This should never happen since the hod.d/<jobid>/env file is
                # written on cluster startup. Maybe someone hacked the dirs.
                self.report_error("Cannot connect to cluster with job ID '%s' yet. It is still queued.", jobid)
            else:
                print "HOD cluster '%s' @ job ID %s appears to be running..." % (label, jobid)

            print "Setting up SSH connection to %s..." % pbsjob.hosts

            # -i: interactive non-login shell
            cmd = ['ssh', '-t', pbsjob.hosts, 'exec', 'bash', '--rcfile', env_script, '-i']
            self.log.info("Logging in using command: %s", ' '.join(cmd))
            os.execvp('/usr/bin/ssh', cmd)

        except StandardError as err:
            self._log_and_raise(err)

        return 0
