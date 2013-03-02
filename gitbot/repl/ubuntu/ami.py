from collections import namedtuple
from itertools import ifilter, groupby
import operator
import re

import requests
import yaml


amidata = namedtuple('amidata', [
    'region',
    'version_name',
    'version',
    'arch',
    'instance_type',
    'release_date',
    'ami_url',
    'aki_id'
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

    reg = operator.attrgetter('region')

    def arch(ami):
        return '32' if ami.arch == 'i386' else '64'

    def ami_id(agroup):
        anchor = agroup.next().ami_url
        return re.match(r'.*>([^<>]*)<.*', anchor).group(1)


    def agrouper(rgroup):
        return {arch: ami_id(agroup)
                    for arch, agroup in groupby(rgroup, key=arch)}

    return {region: agrouper(rgroup)
                for region, rgroup in groupby(ami_list, key=reg)}

__all__ = ['latest']