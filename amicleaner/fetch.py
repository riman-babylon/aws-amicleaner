#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from builtins import object
import boto3
from botocore.config import Config
from .resources.config import BOTO3_RETRIES
from .resources.models import AMI


class Fetcher(object):

    """ Fetches function for AMI candidates to deletion """

    def __init__(self, ec2=None, autoscaling=None):

        """ Initializes aws sdk clients """

        self.ec2 = ec2 or boto3.client('ec2', config=Config(retries={'max_attempts': BOTO3_RETRIES}))
        self.asg = autoscaling or boto3.client('autoscaling')

    def fetch_available_amis(self):

        """ Retrieve from your aws account your custom AMIs"""

        available_amis = dict()

        my_custom_images = self.ec2.describe_images(Owners=['self'])
        for image_json in my_custom_images.get('Images'):
            ami = AMI.object_with_json(image_json)
            available_amis[ami.id] = ami

        return available_amis

    def fetch_lc(self):

        """
        Find all AMIs for launch configurations
        """

        resp = self.asg.describe_launch_configurations()

        amis = [lc.get("ImageId")
                for lc in resp.get("LaunchConfigurations", [])]

        return amis

    def fetch_lt(self):

        """
        Find all AMIs for launch templates
        """

        resp = self.ec2.describe_launch_templates()
        all_lt = [lt.get("LaunchTemplateName", "")
                  for lt in resp.get("LaunchTemplates", [])]

        amis = []
        for lt_name in all_lt:
            resp = self.ec2.describe_launch_template_versions(
                LaunchTemplateName=lt_name
            )
            amis.extend([lt_latest_version.get("LaunchTemplateData", {}).get("ImageId")
                        for lt_latest_version in resp.get("LaunchTemplateVersions", [])])

        return amis

    def fetch_instances(self):

        """ Find AMIs for not terminated EC2 instances """

        resp = self.ec2.describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': [
                        'pending',
                        'running',
                        'shutting-down',
                        'stopping',
                        'stopped'
                    ]
                }
            ]
        )
        amis = [i.get("ImageId", None)
                for r in resp.get("Reservations", [])
                for i in r.get("Instances", [])]

        return amis
