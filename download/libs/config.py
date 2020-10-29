# -*- coding: utf-8 -*-
# __author__ = 'guoquan'
import boto
import boto.s3.connection
import re
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context
import urllib2
import random
import urllib
import hashlib
import time
import json


def get_from_friendly_size(size):
    pattern = re.compile(r'([\d\.]+)([gmk])', re.I)
    match = re.match(pattern, size)
    normal_size = 0
    if match:
        unit = match.group(2)
        if unit.upper() == "G":
            normal_size = int(match.group(1)) * 1024 * 1024 * 1024
        elif unit.upper() == "M":
            normal_size = int(match.group(1)) * 1024 * 1024
        elif unit.upper() == "K":
            normal_size = int(match.group(1)) * 1024
    else:
        pattern = re.compile(r'([\d\.]+)', re.I)
        match = re.match(pattern, size)
        if match:
            normal_size = int(match.group(1))
    return normal_size


def get_sig():
    nonce = str(random.randint(1000, 10000))
    timestamp = str(int(time.time()))
    x_list = ["d2da2f2ca35Gea", timestamp, nonce]
    x_list.sort()
    sha1 = hashlib.sha1()
    map(sha1.update, x_list)
    sig = sha1.hexdigest()
    signature = {
        "client": "rgw",
        "nonce": nonce,
        "timestamp": timestamp,
        "signature": sig
    }
    return urllib.urlencode(signature)

domains = {
    "tsg": "bcl.tsg.com",
    "tsanger": "bcl.tsanger.com",
    "sanger": "bcl.sanger.com",
    "nsanger": "bcl.i-sanger.com"
}


class Config(object):
    def __init__(self, host=None, aws_access_key_id=None, aws_secret_access_key=None, port=80, is_secure=False, threads=10):
        self.host = host
        self.port = port if port else 80
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.is_secure = is_secure
        self.threads = threads
        self._conn = {}
        self._user_conn = None

    def get_rgw_conn(self):
        if not self._user_conn:
            self._user_conn = boto.connect_s3(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                host=self.host,
                port=self.port,
                is_secure=self.is_secure,
                # uncomment if you are not using ssl
                calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                validate_certs=False
            )
        return self._user_conn

    def get_conn_from_bcl(self, region, bucket, type="tsg"):
        if "%s_%s" % (region, bucket) not in self._conn.keys():
            http_handler = urllib2.HTTPHandler()
            https_handler = urllib2.HTTPSHandler()
            opener = urllib2.build_opener(http_handler, https_handler)
            urllib2.install_opener(opener)
            post_data = "%s&%s" % (get_sig(), urllib.urlencode({"region": region, "bucket": bucket}))
            request = urllib2.Request("http://%s/admin/rgw" % domains[type], post_data)
            response = urllib2.urlopen(request, timeout=60)
            data = json.loads(response.read())
            if "success" in data.keys():
                raise Exception("获取RGW连接失败!")
            self._conn["%s_%s" % (region, bucket)] = boto.connect_s3(
                aws_access_key_id=data["aws_access_key_id"],
                aws_secret_access_key=data["aws_secret_access_key"],
                host=data["host"],
                port=data["port"],
                is_secure=data["is_secure"],
                # uncomment if you are not using ssl
                calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                validate_certs=False
            )
        return self._conn["%s_%s" % (region, bucket)]

    def get_rgw_upload_chunk_size(self):
        size = "32M"
        return get_from_friendly_size(size)

    def get_rgw_download_chunk_size(self):
        size = "32M"
        return get_from_friendly_size(size)

    def get_rgw_min_size_to_split(self):
        size = "64M"
        return get_from_friendly_size(size)

    def get_rgw_max_threads(self):
        return 10
