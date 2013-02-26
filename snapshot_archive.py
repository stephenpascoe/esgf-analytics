#!/usr/bin/env python
# BSD Licence
# Copyright (c) 2013, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Crawl the SOLr indexes to get all dataset documents for a particular project
and extract enough information to create a snapshot of the current state.  

Querying SOLr directly should work better than via the esgf search api.

Currently this script assumes dataset versions are not tampered with and that
it is sufficient to extract these values from each dataset:

 1. instance_id
 2. data_node
 3. index_node
 4. size
 6. replica (True of False)
 7. timestamp

"""

import sys
from xml.etree import ElementTree as ET
import urllib2
import json

DUMP_PROPERTIES = ['instance_id', 'data_node', 'index_node', 'size',
                   'replica', 'timestamp']
SOLR_CORE = 'datasets'

BATCH_SIZE = 500
SHARDS_XML = '/esg/config/esgf_shards_static.xml'
ESGF_WHITELIST_NS = "http://www.esgf.org/whitelist"

def get_shards(shards_file=SHARDS_XML):
    shards_xml = ET.parse(open(shards_file))

    for elem in shards_xml.findall('.//{%s}value' % ESGF_WHITELIST_NS):
        yield elem.text

def make_query(shard, core, project, properties, start, rows=BATCH_SIZE):
    url = ('http://{shard}/{core}/select?'
           'q=project:{project}&fl={properties}'
           '&wt=json&start={start}&rows={rows}'.format(
            core=core,
            shard=shard,
            project=project,
            properties=','.join(properties),
            rows=rows, start=start))

    return url

def iter_docs(shard, project, properties, rows=BATCH_SIZE):
    start = 0
    while 1:
        url = make_query(shard, SOLR_CORE, project, properties, start, rows)
        response = urllib2.urlopen(url)
        resp_json = json.load(response)

        for doc in resp_json['response']['docs']:
            yield doc

        num_found = resp_json['response']['numFound']
        if start == 0:
            print '### Num found = %s' % num_found

        start += rows
        if start > num_found:
            return



def main(argv=sys.argv):
    project, outfile = argv[1:]

    shards = get_shards()
    # Override for debug
    #shards = ['localhost:8984/solr']


    with open(outfile, 'w') as fh:
        for shard in shards:
            print '\n## Querying shard %s' % shard
            print >>fh, '#', '\t'.join(DUMP_PROPERTIES)
            for i, result in enumerate(iter_docs(shard, project, DUMP_PROPERTIES)):
                print >>fh, '\t'.join(str(result[x]) for x in DUMP_PROPERTIES)
                if i % BATCH_SIZE == 0:
                    print '[%d]' % (i, ),
                    sys.stdout.flush()


if __name__ == '__main__':
    main()
    
