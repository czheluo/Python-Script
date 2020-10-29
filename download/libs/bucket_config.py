# -*- coding: utf-8 -*-
# __author__ = 'hongdong'

"""获取每个项目对应的bucket--主要用于上传文件的时候，有新的产品上线的时候，一定要在main.conf中添加指定的bucket"""

import ConfigParser
import os
import re


class BucketConfig(object):
    def __init__(self, mode):
        self.rcf = ConfigParser.RawConfigParser()
        if mode == 'nsanger':
            self.rcf.read(os.path.dirname(os.path.realpath(__file__)) + "/nbmain.conf")
        else:
            self.rcf.read(os.path.dirname(os.path.realpath(__file__))+"/main.conf")

    def get_project_region_bucket(self, project_type="default"):
        if self.rcf.has_option("RGW", "%s_bucket" % project_type):
            results = self.rcf.get("RGW", "%s_bucket" % project_type).strip('/').split("://")
        else:
            results = self.rcf.get("RGW", "default_bucket").strip('/').split("://")
        return results[0], results[1]

# if __name__ == "__main__":
#     print BucketConfig().get_project_region_bucket("default")
#     print BucketConfig().get_project_region_bucket("dna_gmap.gmap")
