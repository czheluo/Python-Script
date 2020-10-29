# -*- coding: utf-8 -*-
# __author__ = 'yuguo'
# modified by yuguo at 20170920
# modified by yuguo @ 201806
# last modified by hongdong@20181016
# lated modified by hd@20200820 增加创新平台的数据发送机制

from __future__ import division
import urllib2
import urllib
# import httplib
import sys
import json
# import requests
import os
# import pprint
import re
import random
import time
import hashlib
# from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from basic import Basic
from s3 import S3TransferManager
from bucket_config import BucketConfig
import datetime


class FileLimiter(object):
    def __init__(self, file_obj, read_limit):
        self.read_limit = read_limit
        self.amount_seen = 0
        self.file_obj = file_obj
        self.len = read_limit

    def read(self, amount=-1):
        if self.amount_seen >= self.read_limit:
            return b''
        remaining_amount = self.read_limit - self.amount_seen
        data = self.file_obj.read(remaining_amount if amount < 0 else min(amount, remaining_amount))
        self.amount_seen += len(data)
        return data


class UploadTask(Basic):
    def __init__(self, input_dir, list_path, identity, mode, stream_on, project_type=None, is_new_platform=None):
        """
        self.source_path = /mnt/ilustre/users/sanger-dev/app/bioinfo/WGS
        self.source_dir = WGS
        :param input_dir:
        :param list_path:
        :param identity:
        :param mode:
        :param stream_on:
        :param project_type:
        """
        super(UploadTask, self).__init__('', identity, mode, stream_on)
        self.is_new_platform = False if is_new_platform is None else is_new_platform  # 判断是否是创新平台
        self.url = self.post_url_n if self.is_new_platform else self.post_url
        self.logger.info(self.url)
        self.source_path = input_dir  # 完整路径 /mnt/.../sg-users/./updir
        tmp_list = re.split(r'[\\/]', self.source_path)
        self.source_dir = tmp_list.pop()  # 输入文件夹 /updir
        self._file_info = list()
        self.region, self.bucket = BucketConfig(mode).get_project_region_bucket(project_type)
        self.logger.info('region:{}---bucket:{}'.format(self.region, self.bucket))
        self.target_path = self.post_verifydata()  # rerewrweset/files/m_190/10000001
        self.logger.info("source_path:" + self.source_path)
        self.logger.info("source_dir:" + self.source_dir)
        self.get_file_info(list_path)

    def get_file_info(self, list_path):
        with open(list_path, "rb") as r:
            line = r.next()
            for line in r:
                line = line.rstrip().split("\t")
                d = dict()
                d["path"] = line[0]
                d["size"] = re.sub("B", "", line[1])
                d["description"] = line[2]
                d["locked"] = line[3]
                rel_path = re.sub(self.source_path, "", d["path"]).lstrip("/")
                # rel_path = re.sub(self.source_dir, "", rel_path, 1).lstrip('/')
                d["rel_path"] = rel_path   # \t1.txt
                self.logger.info("rel_path：{}".format(d['rel_path']))
                d["target_path"] = os.path.join(self.target_path, self.source_dir, rel_path)
                self.logger.info("target_path: " + d["target_path"])
                self._file_info.append(d)
        return self._file_info

    def post_verifydata(self):
        """
        请求url: http://api.sg.com/file/verify_filecode
        请求方式:post

        参数：
        $params = array(
            'code'     => 'QAEBXH|702692627ec061cf853b3317bfc1a776',
            'type'     => 'upload', //上传
            'dir_name' => 'abc',  //验证的文件夹名称
        );

        成功时,json结果:
        {
            "success": "true",
            "data": {
                "path": "rerewrweset/files/m_219/10008074"
            }
        }
        """
        my_data = dict()
        my_data["client"] = self.client
        my_data["nonce"] = str(random.randint(1000, 10000))
        my_data["timestamp"] = str(int(time.time()))
        if self.is_new_platform:
            my_data["verify_filecode"] = json.dumps({
                "code": self.identity,
                "type": 'upload',
                "dir_name": self.source_dir
            })
            my_data["binds_id"] = self.binds_id
            my_data["interface_id"] = self.interface_id
            my_data["env_name"] = self.env_name
            x_list = [self.key, my_data["timestamp"], my_data["nonce"]]
        else:
            my_data['code'] = self.identity
            my_data['type'] = 'upload'
            my_data['dir_name'] = self.source_dir
            x_list = [self.client_key, my_data["timestamp"], my_data["nonce"]]
        x_list.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, x_list)
        my_data["signature"] = sha1.hexdigest()
        request = urllib2.Request(self.url, urllib.urlencode(my_data))
        self.logger.info("与{}网站通信， 发送验证码和文件夹名称请求：{}".format(self.url, my_data))
        # self.logger.info("与sanger网站通信， 将上传结果传递至sanger网站上")
        self.logger.info("获取文件夹是否有重名，以及目标存放路径")
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            self.logger.error(e)
            raise Exception(e)
        else:
            the_page = response.read()
            self.logger.info("Return Page:")
            self.logger.info(the_page)
            info = json.loads(the_page)
            self.logger.info(info)
            if info["success"] == 'false':
                self.logger.info(info["m"].encode('utf-8'))
                sys.exit(1)
            else:
                if self.is_new_platform:
                    target_path = json.loads(info["d"])["path"]
                else:
                    target_path = info["data"]["path"]
                self.logger.info("通信成功，获得目标路径:{}".format(target_path))
                if target_path.startswith("rerewrweset") and self.bucket != "rerewrweset":
                    return_path = os.path.join(self.bucket, target_path.split("rerewrweset")[1].lstrip('/'))
                else:
                    return_path = target_path
                return return_path

    def s3_upload_files(self):
        """
        通过s3方式上传文件
        """
        if len(self._file_info) == 0:
            raise ValueError("list为空，没有需要上传的文件，请检查确认！")
        manager = S3TransferManager(use_db=True, bcl_type=self.mode)
        start_time = datetime.datetime.now()
        for d in self._file_info:
            # print "11", d["target_path"]
            manager.add(from_uri=d["path"], to_uri="{}://".format(self.region) + d["target_path"])
        manager.wait()
        self.logger.info("共使用{}s所有文件上传完成!".format((datetime.datetime.now() - start_time).seconds))

    def post_filesdata(self):
        """
        磁盘文件上传成功后，需要请求接口提供文件路径信息：

        请求url: http://api.sg.com/file/add_file_by_code
        请求方式:post
        参数：
        return array(
            'param' => array(
            'code' => 'QAEBXH|702692627ec061cf853b3317bfc1a776',
            'type' => 'upload',
            ),
            'base_path' => 'rerewrweset/files/m_219/10008074',  #前置路径
            'files'     => array(
            array(
                'path' => 'corr_network_calc/corr_network_centrality.txt', //路径
                'size' => '13750',   //大小
                'description' => 'OTU\\u5e8f\\u5217\\u7269\\u79cd\\u5206\\u7c7b\\u6587\\u4ef6', //描述
                'format' => 'taxon.seq_taxon',   //格式
            ),
            array(
                'path' => 'corr_network_calc/corr_network_by_cut.txt',
                'size' => '303363',
                'description' => 'OTU\u5e8f\u5217\u7269\u79cd\u5206\u7c7b\u6587\u4ef6',
                'format' => 'txt',
            ),
            array(
                'path' => 'abc.txt',
                'size' => '1000',
                'description' => 'rererwew',
                'format'      => 'txt',
            )
            ),
            //给相关目录添加描述信息
            'dirs' => array(
            array(
                'path' => 'rerewrweset/files/m_219/10008074/tsanger_3/report_results', //路径
                'description' => '\u57fa\u7840\u5206\u6790\u7ed3\u679c\u6587\u4ef6\u5939', //描述
            ),
            array(
                'path' => 'corr_network_calc',
                'description' => '物种相关性网络分析结果输出目录',
            ),
            ),
        );

        New:
        请求url: http://api.sg.com/file/add_file_by_code
        请求方式:post
        参数：
        return array(
            "basis": {
                "created_ts": "2020-07-28 13:23:09",
                "region": "s3",
                "base_path": "toollab/files/7rq1j4er85ltjp968isqge00q2/l5ief53ktlsq3
                5lou88eui8gh1/interaction_results/plsda_20200728_132158448",
                "code": "11111"
            }
            'files'     => array(
            array(
                'path' => 'corr_network_calc/corr_network_centrality.txt', //路径
                'size' => '13750',   //大小
                'description' => 'OTU\\u5e8f\\u5217\\u7269\\u79cd\\u5206\\u7c7b\\u6587\\u4ef6', //描述
                'format' => 'taxon.seq_taxon',   //格式
            )
            ),
            //给相关目录添加描述信息
            'dirs' => array(
            array(
                'path' => 'rerewrweset/files/m_219/10008074/tsanger_3/report_results', //路径
                'description' => '\u57fa\u7840\u5206\u6790\u7ed3\u679c\u6587\u4ef6\u5939', //描述
            ),
            array(
                'path' => 'corr_network_calc',
                'description' => '物种相关性网络分析结果输出目录',
            ),
            ),
        );
        """
        self.logger.info("post_data: " + self.target_path)
        post_data = dict()
        if self.is_new_platform:
            post_data['basis'] = {
                "created_ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "region": self.region,
                "base_path": os.path.join(self.target_path, self.source_dir),
                'code': self.identity
            }
        else:
            post_data['param'] = {'code': self.identity, 'type': 'upload'}
            post_data['base_path'] = os.path.join(self.target_path, self.source_dir)
            post_data['region'] = self.region
        post_data["files"] = list()
        post_data["dirs"] = list()
        for d in self._file_info:
            post_data["files"].append({"path": d["rel_path"], "format": "", "description": d["description"],
                                       "lock": d["locked"], "size": d["size"]})
        my_data = dict()
        my_data["client"] = self.client
        my_data["nonce"] = str(random.randint(1000, 10000))
        my_data["timestamp"] = str(int(time.time()))
        if self.is_new_platform:
            my_data["binds_id"] = self.binds_id_add
            my_data["interface_id"] = self.interface_id_add
            my_data["env_name"] = self.env_name
            x_list = [self.key_add, my_data["timestamp"], my_data["nonce"]]
            url = self.url
        else:
            x_list = [self.client_key, my_data["timestamp"], my_data["nonce"]]
            url = self.post_add_url
        x_list.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, x_list)
        my_data["signature"] = sha1.hexdigest()
        my_data["sync_files"] = json.dumps(post_data)
        request = urllib2.Request(url, urllib.urlencode(my_data))
        self.logger.info("与{}网站通信， 发送验证码和文件列表：{}".format(url, my_data))
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            self.logger.error(e)
            raise Exception(e)
        else:
            the_page = response.read()
            self.logger.info("Return Page:")
            self.logger.info(the_page)
            my_return = json.loads(the_page)
            if my_return["success"] in ["true", "True", True]:
                self.logger.info("文件上传已经全部结束！")
            else:
                raise Exception("发送网站文件信息失败：{}".format(my_return["m"].encode('utf-8')))
