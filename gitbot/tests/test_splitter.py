# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""
from util import assert_text_equals

from gitbot import splitter


def test_process_simple_text():
    txt = \
'''
def some_function():
    var_1 = 'some value'
    var_2 = "some other value"
    var_3 = var_1
    var_4 = 12
    call_some_other_function()
'''
    split = \
'''{"Fn::Join": ["", [
    "\\ndef some_function():\\n",
    "    var_1 = 'some value'\\n",
    "    var_2 = \\"some other value\\"\\n",
    "    var_3 = var_1\\n",
    "    var_4 = 12\\n",
    "    call_some_other_function()\\n",
    "\\n"
]]}
'''

    out = splitter.split(txt)
    assert_text_equals(out, split)


def test_process_text_with_ref():
    txt = \
'''
def some_function():
    var_1 = '{ "Ref" : "some_value" }'
    var_2 = "{  "Ref": "some_other_value"}"
    var_3 = var_1
    var_4 = {"Ref":"some_int_value"}
    call_some_other_function()
'''
    split = \
'''{"Fn::Join": ["", [
    "\\ndef some_function():\\n",
    "    var_1 = '", {"Ref": "some_value"}, "'\\n",
    "    var_2 = \\"", {"Ref": "some_other_value"}, "\\"\\n",
    "    var_3 = var_1\\n",
    "    var_4 = ", {"Ref": "some_int_value"}, "\\n",
    "    call_some_other_function()\\n",
    "\\n"
]]}
'''

    out = splitter.split(txt)
    assert_text_equals(out, split)

def test_process_text_with_two_refs():
    txt = \
'http://nodejs.org/dist/v{ "Ref": "NodeJSVersion" }/node-v{ "Ref": "NodeJSVersion" }.tar.gz'
    split = \
'''{"Fn::Join": ["", [
    "http://nodejs.org/dist/v", {"Ref": "NodeJSVersion"}, "/node-v", {"Ref": "NodeJSVersion"}, ".tar.gz"
]]}
'''
    out = splitter.split(txt, append_line_break=False)
    assert_text_equals(out, split)    


def test_create_swarm():
    txt = \
'''
#!/bin/bash
/usr/bin/bees up \\
    -k `cat /home/ec2-user/bees_keypair.txt` \\
    -s { "Ref": "BeeCount" } \\
    -z {"Fn::Select" : [ "1", {"Fn::GetAZs" : "" }] } \\
    -g { "Ref" : "BeeSecurityGroup" } \\
    --instance  {"Fn::FindInMap": [ "AWSRegionPlatform2AMI", { "Ref": "AWS::Region" }, "bee"]} \\
    --login ec2-user
'''

    split = \
'''{"Fn::Join": ["", [
    "\\n#!/bin/bash\\n",
    "/usr/bin/bees up \\\\\\n",
    "    -k `cat /home/ec2-user/bees_keypair.txt` \\\\\\n",
    "    -s ", {"Ref": "BeeCount"}, " \\\\\\n",
    "    -z ", {"Fn::Select": ["1", {"Fn::GetAZs": ""}]}, " \\\\\\n",
    "    -g ", {"Ref": "BeeSecurityGroup"}, " \\\\\\n",
    "    --instance  ", {"Fn::FindInMap": ["AWSRegionPlatform2AMI", {"Ref": "AWS::Region"}, "bee"]}, " \\\\\\n",
    "    --login ec2-user\\n",
    "\\n"
]]}
'''

    out = splitter.split(txt)
    assert_text_equals(out, split)


def test_delete_key_pair():
    txt = \
'''
#!/usr/bin/python
import string
import random
import boto.ec2
import os
import sys
if not os.path.exists('/home/ec2-user/bees_keypair.txt'):
     print >> sys.stderr, 'bees_keypair.txt does not exist'
     sys.exit(-1)
with file('/home/ec2-user/bees_keypair.txt', 'r') as f:
     kp_name = f.read().strip()
ec2 = boto.ec2.connect_to_region('{"Ref" : "AWS::Region" }')
ec2.delete_key_pair(kp_name)
os.remove('/home/ec2-user/bees_keypair.txt')
os.remove('/home/ec2-user/.ssh/%s.pem' % kp_name)
print 'Deleted keypair: %s' % kp_name
'''

    split = \
'''{"Fn::Join": ["", [
    "\\n#!/usr/bin/python\\n",
    "import string\\n",
    "import random\\n",
    "import boto.ec2\\n",
    "import os\\n",
    "import sys\\n",
    "if not os.path.exists('/home/ec2-user/bees_keypair.txt'):\\n",
    "     print >> sys.stderr, 'bees_keypair.txt does not exist'\\n",
    "     sys.exit(-1)\\n",
    "with file('/home/ec2-user/bees_keypair.txt', 'r') as f:\\n",
    "     kp_name = f.read().strip()\\n",
    "ec2 = boto.ec2.connect_to_region('", {"Ref": "AWS::Region"}, "')\\n",
    "ec2.delete_key_pair(kp_name)\\n",
    "os.remove('/home/ec2-user/bees_keypair.txt')\\n",
    "os.remove('/home/ec2-user/.ssh/%s.pem' % kp_name)\\n",
    "print 'Deleted keypair: %s' % kp_name\\n",
    "\\n"
]]}
'''

    out = splitter.split(txt)
    assert_text_equals(out, split)


def test_start_swarm():
    txt =\
'''
#!/bin/bash
/usr/bin/bees attack \\
    --url http://{"Fn::GetAtt": [  "ElasticLoadBalancer", "DNSName"  ] }/\\
    -n { "Ref": "TotalConnections" }\\
    --concurrent { "Ref": "ConcurrentConnections" }
'''
    split = \
'''{"Fn::Join": ["", [
    "\\n#!/bin/bash\\n",
    "/usr/bin/bees attack \\\\\\n",
    "    --url http://", {"Fn::GetAtt": ["ElasticLoadBalancer", "DNSName"]}, "/\\\\\\n",
    "    -n ", {"Ref": "TotalConnections"}, "\\\\\\n",
    "    --concurrent ", {"Ref": "ConcurrentConnections"}, "\\n",
    "\\n"
]]}
'''
    out = splitter.split(txt)
    assert_text_equals(out, split)


def test_boto():
    txt =\
'''
[Credentials]
aws_access_key_id = { "Ref": "CfnKeys" }
aws_secret_access_key = {"Fn::GetAtt": ["CfnKeys", "SecretAccessKey"] }
[Boto]
ec2_region_name = { "Ref" : "AWS::Region" }
ec2_region_endpoint = ec2.{ "Ref" : "AWS::Region" }.amazonaws.com
elb_region_name = { "Ref" : "AWS::Region" }
elb_region_endpoint = elasticloadbalancing.{ "Ref" : "AWS::Region" }.amazonaws.com
'''
    split = \
'''{"Fn::Join": ["", [
    "\\n[Credentials]\\n",
    "aws_access_key_id = ", {"Ref": "CfnKeys"}, "\\n",
    "aws_secret_access_key = ", {"Fn::GetAtt": ["CfnKeys", "SecretAccessKey"]}, "\\n",
    "[Boto]\\n",
    "ec2_region_name = ", {"Ref": "AWS::Region"}, "\\n",
    "ec2_region_endpoint = ec2.", {"Ref": "AWS::Region"}, ".amazonaws.com\\n",
    "elb_region_name = ", {"Ref": "AWS::Region"}, "\\n",
    "elb_region_endpoint = elasticloadbalancing.", {"Ref": "AWS::Region"}, ".amazonaws.com\\n",
    "\\n"
]]}
'''
    out = splitter.split(txt)
    assert_text_equals(out, split)
