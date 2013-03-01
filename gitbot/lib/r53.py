from boto.route53.connection import Route53Connection
from boto.route53.record import ResourceRecordSets
from commando.util import getLoggerWithConsoleHandler

logger = getLoggerWithConsoleHandler('gitbot.lib.r53')

s3zones = {

    "us-east-1": "Z3AQBSTGFYJSTF",
    "us-west-2": "Z3BJ6K6RIION7M",
    "us-west-1": "Z2F56UZL2M1ACD",
    "eu-west-1": "Z1BKCTXD74EZPE",
    "ap-southeast-1": "Z3O0J2DXBE1FTB",
    "ap-southeast-2": "Z1WCIGYICN2BYD",
    "ap-northeast-1": "Z2M4EHUR26P7ZW",
    "sa-east-1": "Z7KQH4QJS55SO",
    "us-gov-west-1": "Z31GFT0UA1I2HV"

}

class Route(object):

    def __init__(self, zone_name, **kwargs):
        try:
            self.connection = Route53Connection(**kwargs)
        except:
            raise Exception(
                'Please setup AWS security credentials in your environment.'
                'Add this to your startup file or virtualenv activate script:'
                'AWS_ACCESS_KEY_ID=<your aws key>'
                'AWS_SECRET_ACCESS_KEY=<your aws secret>'
                'export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY')
        self.zone = self.connection.get_zone(zone_name)


    def add_route_to_bucket(self, bucket_name, region='us-east-1'):
        s3zone = s3zones[region]
        changes = ResourceRecordSets(self.connection, self.zone.id)
        change = changes.add_change('CREATE',
                    bucket_name + '.',
                    'A',
                    alias_dns_name='s3-website-'+ region + '.amazonaws.com.',
                    alias_hosted_zone_id=s3zone)
        changes.commit()

    def delete_route_to_bucket(self, bucket_name, region='us-east-1'):
        s3zone = s3zones[region]
        changes = ResourceRecordSets(self.connection, self.zone.id)
        change = changes.add_change('DELETE',
                    bucket_name + '.',
                    'A',
                    alias_dns_name='s3-website-'+ region + '.amazonaws.com.',
                    alias_hosted_zone_id=s3zone)
        changes.commit()