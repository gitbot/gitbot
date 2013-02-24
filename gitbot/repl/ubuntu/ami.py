from collections import namedtuple
from itertools import ifilter, groupby

import requests
import yaml


amidata = namedtuple('amidata', [
    'region',
    'version_name',
    'version',
    'arch',
    'instance_type',
    'release_date',
    'url',
    'id'
])

def latest(version_name='precise', instance_type='ebs'):
    response = requests.get(
                'http://cloud-images.ubuntu.com/locator/ec2/releasesTable')
    if not response.status_code == 200:
        print 'Cannot load Ubuntu AMI list'
        return None

    ami_list =  yaml.load(response.text)['aaData']

    def matcher(ami):
        return ami.version_name == version_name and \
                ami.instance_type == instance_type

    ami_list = ifilter(matcher, (amidata(*ami) for ami in ami_list))

    def grouper(ami):
        return (ami.region, '32' if ami.arch == 'i386' else '64')


    return {region: {arch: group.next().id}
                for (region, arch), group in groupby(ami_list, key=grouper)}