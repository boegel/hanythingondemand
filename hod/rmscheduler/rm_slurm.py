# #
# Copyright 2019-2019 Ghent University
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
Implementation of the Slurm resource manager

@author: Kenneth Hoste (Ghent University)
"""
import os
import re
import tempfile
from vsc.utils import fancylogger

from hod.commands.command import Squeue
from hod.rmscheduler.resourcemanagerscheduler import ResourceManagerScheduler


_log = fancylogger.getLogger(fname=False)


class SlurmJob(object):
    '''
    Data type representing a job
    '''
    __slots__ = ['jobid', 'state', 'hosts']

    def __init__(self, jobid, jstate, hosts):
        self.jobid = jobid
        self.state = jstate
        self.hosts = hosts

    def __str__(self):
        return "Jobid %s state %s ehosts %s" % (self.jobid, self.state, self.hosts)

    def __repr__(self):
        return 'SlurmJob(jobid=%s, state=%s, hosts=%s)' % (self.jobid, self.state, self.hosts)


def format_state(jobs):
    '''Given a list of SlurmJob objects, print them.'''
    temp = "Id %s State %s Node %s"
    if len(jobs) == 0:
        msg = "No jobs found."
    elif len(jobs) == 1:
        job = jobs[0]
        msg = "Found 1 job " + temp % (job.jobid, job.state, job.hosts)
    else:
        msg = "Found %s jobs\n" % len(jobs)
        for j in jobs:
            msg += "    %s\n" + temp % (j.jobid, j.state, j.hosts)
    _log.debug("msg %s", msg)

    return msg


class Slurm(ResourceManagerScheduler):
    """Interaction with torque"""
    def __init__(self, options):
        super(Slurm, self).__init__(options)
        self.log = fancylogger.getLogger(self.__class__.__name__, fname=False)
        self.options = options
        self.log.debug("Provided options %s", options)

        self.vars = {
            'cwd': 'SLURM_SUBMIT_DIR',
            'jobid': 'SLURM_JOBID',
        }

    def submit(self, txt):
        """Submit the jobscript txt, set self.jobid"""
        self.log.debug("Going to submit script %s", txt)

        fh, scriptfn = tempfile.mkstemp()
        f = os.fdopen(fh, 'w')
        self.log.debug("Writing temp jobscript to %s" % scriptfn)
        f.write(txt)
        f.close()

        self.jobid = None  # FIXME replace with submission command
        self.log.debug("Succesful jobsubmission returned jobid %s", self.jobid)

        os.remove(scriptfn)

    def state(self, jobid=None, job_filter=None):
        """Return the state of job with id jobid"""
        if jobid is None:
            jobid = self.jobid

        state = self.info(jobid, types=['job_state', 'exec_host'], job_filter=job_filter)

        jid = [x['id'] for x in state]

        jstate = [x.get('job_state', None) for x in state]

        def get_uniq_hosts(txt, num=1):
            """txt host1/cpuid+host2/cpuid
                - num: number of nodes to return
            """
            res = []
            for h_c in txt.split('+'):
                h = h_c.split('/')[0]
                if h in res:
                    continue
                res.append(h)
            return res[:num]

        ehosts = [get_uniq_hosts(x.get('exec_host', '')) for x in state]

        self.log.debug("Jobid  %s jid %s state %s ehosts %s (%s)", jobid, jid, jstate, ehosts, state)

        def _first_or_blank(x):
            '''Only use first node (don't use [0], job in Q have empty list'''
            return '' if len(x) == 0 else x[0]

        jobs = [SlurmJob(j, s, h) for (j, s, h) in zip(jid, jstate, map(_first_or_blank, ehosts))]
        return jobs

    def list_jobs(self):
        """Return list of currently queued/running jobs."""

        # https://gist.github.com/stevekm/7831fac98473ea17d781330baa0dd7aa
        stdout, _ = Squeue().run()

        # expected format:
        # CLUSTER: cluster_name
        # LABEL1|LABEL2|...
        # job1_value1|job1_value2|...
        # job2_value1|job2_value2|...

        lines = stdout.splitlines()

        # first line can be ignored
        lines.pop(0)

        # 2nd line is name of fields
        keys = lines.pop(0).split('|')

        jobs = []
        for line in lines:
            values = line.split('|')
            job = dict((key, val) for key, val in zip(keys, values))
            jobs.append(job)

        return jobs

    def info(self, jobid, types=None, job_filter=None):
        """Return jobinfo"""

        if job_filter is None:
            job_filter = {}
        self.log.debug("Job filter passed %s", job_filter)
        if self.job_filter is not None:
            self.log.debug("Job filter update with %s", self.job_filter)
            job_filter.update(self.job_filter)
        self.log.debug("Job filter used %s", job_filter)

        # only known filter is based on job name
        job_name_filter = job_filter.pop('Job_Name', None)
        if job_filter:
            raise NotImplementedError("Unknown job filter keys encountered: %s" % job_filter.keys())

        # get list of jobs
        jobs = self.list_jobs()
        import pprint
        pprint.pprint(jobs)

        res = []
        for job in jobs:
            job_details = {}
            if job_name_filter:
                regex = re.compile(job_name_filter)
                if regex.search(job['NAME']):
                    res.append(job_details)

        self.log.info("Found job info %s", res)
        return res

    def remove(self, jobid=None):
        """Remove the job with id jobid."""
        if jobid is None:
            jobid = self.jobid

        raise NotImplementedError

        return False  # FIXME return True if removal worked

    def header(self):
        """Return the script header that requests the properties.
           nodes = number of nodes
           ppn = ppn (-1 = full node)
           walltime = time in hours (can be float)
        """
        nodes = self.options.get('nodes', 50)
        ppn = self.options.get('ppn', -1)
        walltime = self.options.get('walltime', 72)
        mail = self.options.get('mail', [])
        mail_others = self.options.get('mailothers', [])
        queue = self.options.get('queue', 'default')
        partition = self.options.get('partition', 'default')
        account = self.options.get('account', 'default')
        reservation = self.options.get('reservation', None)

        self.log.debug("nodes %s, ppn %s, walltime %s, mail %s, mail_others %s, queue %s, partition %s, account %s",
                       nodes, ppn, walltime, mail, mail_others, queue, partition, account)
        if nodes is None:
            nodes = 1

        if ppn is None:
            ppn = 1

        raise NotImplementedError  # FIXME (stuff below hasn't been cleaned up yet to match Slurm)

        walltime = int(float(walltime) * 60 * 60)  # in hours
        m, s = divmod(walltime, 60)
        h, m = divmod(m, 60)
        # d, h = divmod(h, 24) ## no days
        # also prints leading 0s (do not insert if x > 0 (eg print 1:0)!
        # walltimetxt = ":".join(["%02d" % x for x in [ d,h, m, s]]) ## no days
        walltimetxt = ":".join(["%02d" % x for x in [h, m, s]])

        self.log.debug("Going to generate for nodes %s, ppn %s, walltime %s",
                       nodes, ppn, walltimetxt)

        self.args = {'resources': {'walltime': walltimetxt,
                                   'nodes': '%d:ppn=%d' % (nodes, ppn)
                                   },
                     }

        if queue:
            self.args['queue'] = queue

        if partition:
            self.args['resources']['partition'] = partition

        if account:
            self.args['account'] = account

        if mail or mail_others:
            self.args['mail'] = {}
            if not mail:
                mail = ['e']
            self.args['mail']['send'] = ''.join(mail)
            if mail_others:
                self.args['mail']['others'] = ','.join(mail_others)

        if reservation:
            self.args['reservation'] = reservation

        self.log.debug("Create args %s", self.args)

        # # creating the header. Not used in submission!!
        opts = []
        for arg in self.args.keys():
            if arg in ('resources',):
                for k, v in self.args[arg].items():
                    opts.append("-l %s=%s" % (k, v))
            elif arg in ('mail',):
                opts.append('-m %s' % self.args[arg]['send'])
                if 'others' in self.args[arg]:
                    opts.append('-M %s' % self.args[arg]['others'])
            elif arg in ('queue',):
                if self.args[arg]:
                    opts.append('-q %s' % self.args[arg])
            elif arg in ('account',):
                if self.args[arg]:
                    opts.append('-A %s' % self.args[arg])
            elif arg in ('reservation',):
                if self.args[arg]:
                    opts.append('-W x=FLAGS:ADVRES:%s' % self.args[arg])
            else:
                self.log.debug("Unknown arg %s. Not adding to args.", arg)

        hdr = ["#SBATCH %s" % o for o in opts]
        self.log.debug("Created job script header %s", hdr)
        return hdr

    def get_ppn(self):
        """Guess the ppn for full node"""
        raise NotImplementedError
