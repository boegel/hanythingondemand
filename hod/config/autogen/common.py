##
# Copyright 2009-2015 Ghent University
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
##
"""
Common functions for autogenerated configurations.

@author: Ewan Higgs (Ghent University)
"""

from os.path import dirname
from collections import namedtuple
import errno
import os
import re
import math

def parse_memory(memstr):
    '''
    Given a string representation of memory, return the memory size in
    bytes. It supports up to terabytes.

    No size defaults to byte:

    >>> parse_memory('200')
    200

    Also supports k for kilobytes:

    >>> parse_memory('200k')
    204800


    kb, mb, gb, tb, etc also works:

    >>> parse_memory('200kb')
    204800
    '''
    size = re.search(r'[bBkKmMgGtT]', memstr)
    if size is not None:
        coef = float(memstr[:size.start()])
        exp = memstr[size.start():size.end()]
    else:
        try:
            coef = float(memstr)
        except ValueError:
            raise RuntimeError('Unable to parse memory string:', memstr)
        exp = ''

    if exp in ['', 'b', 'B']:
        return coef
    elif exp in ['k', 'K']:
        return coef * 1024
    elif exp in ['m', 'M']:
        return coef * (1024 ** 2)
    elif exp in ['g', 'G']:
        return coef * (1024 ** 3)
    elif exp in ['t', 'T']:
        return coef * (1024 ** 4)
    # Should not be able to get here
    raise RuntimeError('Unable to parse memory amount:', memstr) # pragma: no cover


# mapping for total system memory -> reserved for OS
# Retrieved from:
# http://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.0.6.0/bk_installing_manually_book/content/rpm-chap1-11.html
MemRec = namedtuple('MemRec', ['total', 'os'])
_RECOMMENDATIONS = [
    MemRec(parse_memory('8g'), parse_memory('2g')),
    MemRec(parse_memory('16g'), parse_memory('2g')),
    MemRec(parse_memory('24g'), parse_memory('4g')),
    MemRec(parse_memory('48g'), parse_memory('6g')),
    MemRec(parse_memory('64g'), parse_memory('8g')),
    MemRec(parse_memory('72g'), parse_memory('8g')),
    MemRec(parse_memory('96g'), parse_memory('12g')),
    MemRec(parse_memory('128g'), parse_memory('24g')),
    MemRec(parse_memory('256g'), parse_memory('32g')),
    MemRec(parse_memory('512g'), parse_memory('64g')),
]

def blocksize(path):
    '''
    Find the block size for the file system given a path. If the path points to
    a directory that does not yet exist, use the parent directory under the
    assumption that the provided path will appear later on the existing file
    system (as opposed to being a new mount).
    '''
    try:
        return os.statvfs(path).f_bsize
    except OSError, e:
        if e.errno == errno.ENOENT:
            return os.statvfs(dirname(path)).f_bsize
        raise

def reserved_memory(totalmem):
    '''
    Given an amount of memory in bytes, return the amount of memory that
    should be reserved by the operating system (also in bytes).
    '''
    for mem in _RECOMMENDATIONS:
        if totalmem <= mem.total:
            return mem.os
    # totalmem > 512g
    return _RECOMMENDATIONS[-1].os


def available_memory(node):
    '''
    Return the amount of memory available in bytes. There are three things we
    consider: 
    1. If we are using all the cores, we assume we can use all the
    memory in the machine (minus what the OS needs).

    2. If ulimit is set and less than meminfo, we use it, we use it.

    3. If ulimit for vmem is not set (unlimited) then we use the amount of
    available memory according based on total machine memory scaled by
    usablecpus/totalcpus
    '''
    meminfo = node['memory']['meminfo']['memtotal']
    memory = meminfo - reserved_memory(meminfo)
    # If we have the whole box, let's use all the non OS memory
    if node['cores'] == node['totalcores']:
        return memory

    pct_cores = float(node['cores']) / node['totalcores']

    memory = int(memory * pct_cores)
    ulimit = node['memory']['ulimit']
    if ulimit == 'unlimited':
        return int(memory)
    else:
        return min(int(memory), int(ulimit))

def set_default(d, key, val):
    '''If a value is not in dict d, set it'''
    if key not in d:
        d[key] = val
    return d

def update_defaults(d1, d2):
    '''Update dict d1 with data from d2 iff values are not already in d1.'''
    for k, v in d2.items():
        set_default(d1, k, v)
    return d1

def format_memory(mem, round_val=False):
    '''
    Given an integer 'mem' for the amount of memory in bytes, return the string
    with associated units. If round_val is set, then the value will be rounded
    to the nearest unit where mem will be over 1.

    Note that this is used to set heap sizes for the jvm which doesn't accept
    non integer sizes. Therefore this truncates.

    Note also that this supports outputting 'b' for bytes even though java
    -Xmx${somenum}b won't work.
    '''
    units = 'bkmgt'
    unit_idx = len(units) - 1
    while unit_idx > 0:
        mem_in_units = mem/(1024.**unit_idx)
        if mem >= (1024**unit_idx):
            if round_val:
                return '%d%s' % (round(mem_in_units), units[unit_idx])
            elif mem_in_units - int(mem_in_units) == 0:
                return '%d%s' % (mem_in_units, units[unit_idx])
        unit_idx -= 1
    return '%db' % mem

def round_mb(mem):
    '''
    Given memory amount in bytes, round to the best mb value based on
    Hortonworks' script:
    https://github.com/hortonworks/hdp-configuration-utils
    '''
    mem_in_mb = mem / (1024**2)
    if mem_in_mb > 4096:
        denom = 1024
    elif mem_in_mb > 2048:
        denom = 512
    elif mem_in_mb > 1024:
        denom = 256
    else:
        denom = 128

    return int(math.floor(mem_in_mb/denom) * denom)

def cap(val, limit):
    '''
    Return val unless val is over the limit; then return the limit.
    '''
    if val > limit:
        return limit
    else:
        return val

