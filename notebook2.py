# BSD Licence
# Copyright (c) 2013, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # Analysis of CMIP5 archive snapshot 2013-02-19
# 
# Author: Stephen Pascoe
# 
# By directly querying the SOLr shards at http://esgf-index1.ceda.ac.uk I have extracted summary information for every dataset version in the CMIP5 archive.

# <codecell>

import pandas as p
import matplotlib.pyplot as plt
import numpy as np

# <codecell>

%%sh
head -n 3 cmip5_snapshot-20130219.dat

# <codecell>

archive = p.read_csv('cmip5_snapshot-20130219.dat', sep='\t', skiprows=1, parse_dates=True,
    names=['instance_id', 'data_node', 'index_node', 'size', 'replica', 'timestamp'],
)
# Convert to GB
archive['size'] = archive['size'] / 1000000000

print 'Total CMIP5 archive volume (all versions) = %.0f TB' % (float(archive['size'].sum()) / 1000, )

# <codecell>

g = archive.groupby('data_node')
g.agg({
    'size': sum,
    'replica': sum,
    'instance_id': len
    })

# <codecell>

# Split the archive into dataset_id and version
def split_instance_id(instance_id):
    parts = instance_id.split('.')
    return '.'.join(parts[:-1]), int(parts[-1][1:])
archive['dataset_id'] = archive['instance_id'].map(lambda x: split_instance_id(x)[0])
archive['version'] = archive['instance_id'].map(lambda x: split_instance_id(x)[1])
archive['institute'] = archive['instance_id'].map(lambda x: x.split('.')[2])

# <codecell>

# Consider just replicas
replicas = archive[archive['replica']==True]

replicas_g = replicas.groupby(['institute', 'data_node'])
replica_counts = replicas_g['instance_id'].agg(len)
replica_counts = replica_counts.unstack()
replica_counts.fillna(0, inplace=True)
replica_counts['dkrz'] = (replica_counts['albedo2.dkrz.de'] + 
                            replica_counts['bmbf-ipcc-ar5.dkrz.de'] + 
                            replica_counts['cmip3.dkrz.de'])
del replica_counts['albedo2.dkrz.de']
del replica_counts['bmbf-ipcc-ar5.dkrz.de']
del replica_counts['cmip3.dkrz.de']
replica_counts.columns = ['badc', 'pcmdi', 'dkrz']
replica_counts

# <codecell>

fig = plt.figure(figsize=(16,6))
ax = fig.add_subplot(1,2,1)
bars = replica_counts.transpose().plot(kind='bar', stacked=True, ax=ax)
for i, patch in enumerate(bars.patches):
    hatches = ['', '/', '//', '\\', '\\\\', '+', 'x']
    j = i // 4 % 7
    patch.set_hatch(hatches[j])
ax.legend(loc='center left', bbox_to_anchor=(1, 0.6), ncol=2)
ax.set_title('Number of published dataset versions partitioned by institute')

# <rawcell>

# 
# 
# 
# 
# 
# 
# 
# 
# 
# 

# <codecell>

replicas_ondisk = p.load('replicas_ondisk.pandas')

# <codecell>

fig = plt.figure(figsize=(16,10))
ax = fig.add_subplot(2,2,1)
bars = replica_counts.transpose().plot(kind='bar', stacked=True, ax=ax)
for i, patch in enumerate(bars.patches):
    hatches = ['', '/', '//', '\\', '\\\\', '+', 'x']
    j = i // 4 % 7
    patch.set_hatch(hatches[j])
ax.legend(loc='center left', bbox_to_anchor=(1, 0.6), ncol=2)
ax.set_ylim((0, 60000))
ax = fig.add_subplot(2,2,3)
bars = replicas_ondisk.transpose().plot(kind='bar', stacked=True, ax=ax)
for i, patch in enumerate(bars.patches):
    hatches = ['', '/', '//', '\\', '\\\\', '+', 'x']
    j = i // 4 % 7
    patch.set_hatch(hatches[j])
ax.legend(loc='center left', bbox_to_anchor=(1, 0.6), ncol=2)
ax.set_title('Number of latest datasets on disk partitioned by institute')

# <codecell>


