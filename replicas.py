# BSD Licence
# Copyright (c) 2013, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # Analysis of replicated CMIP5 datasets on 2013-02-06
# **Author**: [Stephen Pascoe](Stephen.Pascoe@stfc.ac.uk)
# 
# This notebook describes the analysis of a snapshot of all replicas in the CMIP5 archive on February 6th 2013.  A list of all dataset versions at each of the 3 replicating data centres is read, analysed and compared with the total number of datasets listed in the CMIP5 archive.  
# 
# This analysis uses the following terminology:
# 
# * **Dataset**: A unit of data published into the system.
# * **Dataset Version**: A particular version of a dataset.  Each dataset version has a datestamp and datasets can be updated by publishing new dataset versions.
# * **Latest dataset**: The dataset version which is the most up to date of a particular dataset.
# 
# ## Initation and data import

# <codecell>

import pandas as p
import matplotlib.pyplot as plt
import itertools as itr
from glob import glob
import os.path as op

from matplotlib_venn import venn3
from pyesgf.search import SearchConnection

class IdentifierMap(dict):
    """
    An identifier map D is a dictionary of sets such that:
    
      D[data_centre] = set([id1, id2, ...])

    ids can be drs_ids, dataset_ids, etc.

    """

    def make_venn(self):
        """
        Create a venn diagram from a dictionary of replica sets
        """

        subsets = self._subsets()
        # Remap rows with binary codes
        def binkey(row):
            b = [0, 0, 0]
            keys = self.keys()
            for r in row:
                b[keys.index(r)] = 1

            return ''.join(str(x) for x in b)

        subsets_remapped = dict((binkey(k), v) for (k, v) in subsets.items())

        return (venn3(subsets=subsets_remapped, set_labels = self.keys()), subsets)
    
    def _subsets(self):
        rows = list(reduce(itr.chain, (itr.combinations(self, n) 
                                       for n in range(1, len(self) + 1))))
        return dict((x, len(self._exclusive_intersect(x))) for x in rows)
    
    def _exclusive_intersect(self, keys):
        """
        Returns the set of ids that intersect with all given keys and not any 
        other key in self.

        """
        #inc_s = reduce(lambda x, y: x.intersection(y), 
        #               (self[x] for x in keys))
        inc_s = self[keys[0]].copy()
        for other_key in self:
            if other_key in keys:
                inc_s.intersection_update(self[other_key])
            else:
                inc_s.difference_update(self[other_key])

        return inc_s

    def add_fromfile(self, key, filepath):
        """
        Add identifiers for the given key from the contents of filepath.
        If there is already ids for that key the set will be added to.

        """
        with open(filepath) as fh:
            target_set = self.setdefault(key, set())
            for line in fh:
                self[key].add(line.strip())
            

    def by_institute(self):
        """
        Return a dictionary of sets where each key is the institute.
        Account for some naming anomalies.
        
        """
        institute_latest = {}
        for centre in self:
            institutes = institute_latest[centre] = {}
            for drs in self[centre]:
                parts = drs.split('.')
                if parts[0] != 'cmip5':
                    continue
                if len(parts) == 10:
                    (activity, product, institute, model, experiment, frequency, realm, table, ensemble, version) = parts
                else:
                    (activity, product, institute, model, experiment, frequency, realm, table, ensemble) = parts
                # Account for metadata anomalies
                institute = institute.lower()
                if institute == 'noaa-ncep':
                    institute == 'ncep'
                institutes.setdefault(institute, set()).add(drs)

        institute_counts = {}
        for c in institute_latest:
            institute_counts[c] = dict((k, len(v)) for (k, v) in institute_latest[c].items())
        df_institute = p.DataFrame(institute_counts)

        return df_institute


def plot_venn(replicas, replicas_ds, replicas_latest):
    fig = plt.figure(figsize=(10,10))
    ax1 = fig.add_subplot(2,2,1)
    ax1.set_title('Replicated Dataset Versions by Centre')
    venn_dv, subsets_dv = replicas.make_venn()
    ax2 = fig.add_subplot(2,2,2)
    ax2.set_title('Replicated Datasets by Centre')
    venn_ds, subsets_ds = replicas_ds.make_venn()
    ax3 = fig.add_subplot(2,2,3)
    ax3.set_title('Replicated Latest Dataset Versions by Centre')
    venn_latest, subsets_latest = replicas_latest.make_venn()
    df = p.DataFrame({
            'dataset versions': subsets_dv,
            'datasets': subsets_ds,
            'latest datasets': subsets_latest
            })
    return fig, df



##############################################################################
# Main

replica_lists = glob('data/*_replicated_dataset_versions-*.txt')

replicas = IdentifierMap()       
replicas_ds = IdentifierMap()
latest = {}
replicas_latest = IdentifierMap()

for replica_list in replica_lists:
    centre = op.basename(replica_list).split('_')[0]
    replicas.add_fromfile(centre, replica_list)

# These counts no not include the original datasets for MOHC heald at BADC
# or the MPI-M datasets held at DKRZ.  To account for this we add all the 
# MOHC output1 dataset versions held at BADC.
replicas.add_fromfile('badc', 'data/badc_mohc_output1.txt')
replicas.add_fromfile('dkrz', 'data/dkrz_mpih_output1.txt')


#
# Construct the replicas_latest and replicas_ds maps
#
for c in replicas:
    ds_iter = ('.'.join(x.split('.')[:-1]) for x in replicas[c])
    replicas_ds[c] = set(ds_iter)
    
for dv in replicas['badc'] | replicas['dkrz'] | replicas['pcmdi']:
    version = int(dv.split('.')[-1][1:])
    ds = '.'.join(dv.split('.')[:-1])
    latest[ds] = max(latest.get(ds, 0), version)

for c in replicas:
    s = replicas_latest[c] = set()
    for dv in replicas[c]:
        version = int(dv.split('.')[-1][1:])
        ds = '.'.join(dv.split('.')[:-1])
        if version == latest[ds]:
            s.add(dv)

# Aggregate set sizes
replica_counts = p.DataFrame({
        'dataset versions': dict((k, len(v)) for (k, v) in replicas.items()),
        'datasets': dict((k, len(v)) for (k, v) in replicas_ds.items()),
        'latest datasets': dict((k, len(v)) for (k, v) in replicas.items()),
        })

# ## Intersection of dataset replicas
# 
# We plot the venn diagrams showing the intersection of datasets, dataset versions and latest datasets at each centre.

# <codecell>

fig, df = plot_venn(replicas, replicas_ds, replicas_latest)

# ## Breakdown of holdings by institute
# 
# We now concentrate on the latest datasets and create a breakdown of the statistics by institute

df_institute = replicas_latest.by_institute()









"""
# <markdowncell>

# We now add the counts of all non-replicas in the archive by querying the ESGF Search API.
# 
# It should be noted at this point that we are making 2 assumptions when comparing these figures:
# 
#  1. That no replicated latest dataset has been deprecated by a subsequent version.  This is unlikely to be the case as some updates to datasets have almost certainly not been replicated.
#  2. That no dataset exists only as a replica.  I.e. that no dataset has been replicated and then it's original removed.

# <codecell>

conn = SearchConnection('http://pcmdi9.llnl.gov/esg-search')
ctx = conn.new_context(project='CMIP5', product='output1', latest=True, replica=False)
facet_counts = ctx.facet_counts

df_institute['archive output1'] = p.Series(facet_counts['institute'].values(), 
                                   (x.lower() for x in facet_counts['institute'].keys()))

df_institute

# <markdowncell>

# We can plot this data to emphasise the total replica of coverage and the coverage per institute

# <codecell>

fig = plt.figure(figsize=(16,6))
ax = fig.add_subplot(1, 2, 1)
bars = df_institute.transpose().plot(kind='bar', stacked=True, ax=ax)
for i, patch in enumerate(bars.patches):
    hatches = ['', '/', '//', '\\', '\\\\', '+', 'x']
    j = i // 4 % 7
    patch.set_hatch(hatches[j])


# Put a legend to the right of the current axis
ax.legend(loc='center left', bbox_to_anchor=(1, 0.6), ncol=2)
ax.set_title('Number of latest datasets by centre, partitioned by institute')

# <codecell>

fig = plt.figure(figsize=(14,6))
ax = fig.gca()
df_institute.plot(kind='bar', ax=ax)
ax.legend(loc='upper right')
ax.set_title('Number of latest datasets replicated at each centre by institute')

# <codecell>


"""
