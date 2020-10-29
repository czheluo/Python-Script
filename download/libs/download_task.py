# -*- coding: utf-8 -*-
# __author__ = 'xuting'
# modified by yuguo at 20170719
# modified by yuguo at 20170920
# modified by hd @ 20200821

from __future__ import division
import urllib2
import urllib
# import httplib
import sys
import json
# import requests
import os
import re
# import errno
import random
import time
import hashlib
from basic import Basic
from s3 import S3TransferManager
import datetime


class DownloadTask(Basic):
    """
    用于内部下载平台上的文件
    """
    def __init__(self, identity, outpath, mode, stream_on, is_new_platform):
        super(DownloadTask, self).__init__(outpath, identity, mode, stream_on)
        self._file_list = list()
        self.is_new_platform = is_new_platform
        self.url = self.post_url_n if self.is_new_platform else self.post_url
        self.outpath = outpath
        if mode == 'tsg':
            self._basepath = 'http://bcl.tsg.com/pdata/'
        elif mode == 'tsanger':
            self._basepath = 'http://bcl.tsanger.com/pdata/'
        else:
            self._basepath = 'http://bcl.sanger.com/pdata/'

    def post_verifydata(self):
        """
        验证下载码：
        请求url: http://api.sg.com/file/verify_filecode
        请求方式:post
        参数：
        $params = array(
            'code'     => 'ATWKZN|e0cac412c4956c0879f2025b51d2024b',
            'type'     => 'download', //下载
        );
        成功时返回的数据：
        {
            "success": "true",
            "data": {
                "files": [
                    {
                        "file_name": "seqs_tax_assignments.txt",
                        "current_path": "sanger_15004/cmd_112_1493109842/output/Tax_assign/",
                        "disk_url": "rerewrweset/files/m_193/10007924/i-sanger_14621/cmd_112_1493109842/output/
                        Tax_assign/seqs_tax_assignments.txt"
                    },
                    {
                        "file_name": "valid_sequence.txt",
                        "current_path": "sanger_15004/cmd_112_1493109842/output/QC_stat/",
                        "disk_url": "rerewrweset/files/m_193/10007924/i-sanger_14621/cmd_112_1493109842/output/
                        QC_stat/valid_sequence.txt"
                    },
                    ...
                ]
            }
        }
        """
        my_data = dict()
        my_data['client'] = self.client
        my_data['nonce'] = str(random.randint(1000, 10000))
        my_data['timestamp'] = str(int(time.time()))
        if self.is_new_platform:
            my_data["verify_filecode"] = json.dumps({
                "code": self.identity,
                "type": 'download',
            })
            my_data["binds_id"] = self.binds_id
            my_data["interface_id"] = self.interface_id
            my_data["env_name"] = self.env_name
            x_list = [self.key, my_data['timestamp'], my_data['nonce']]
        else:
            my_data['code'] = self.identity
            my_data['type'] = 'download'
            x_list = [self.client_key, my_data['timestamp'], my_data['nonce']]
        x_list.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, x_list)
        my_data['signature'] = sha1.hexdigest()
        request = urllib2.Request(self.url, urllib.urlencode(my_data))
        self.logger.info("与{}网站通信， 发送下载验证请求：{}".format(self.url, my_data))
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            self.logger.error(e)
            raise Exception(e)
        else:
            the_page = response.read()
            self.logger.info("Return Page:")
            self.logger.info(the_page)
            # my_return = json.loads(the_page)
            # print my_return
            info = json.loads(the_page)
            if not info["success"]:
                self.logger.info(info["m"])
                sys.exit(1)
            else:
                print info
                self.logger.info("通信成功，获得文件列表")
                if self.is_new_platform:
                    self._file_list = json.loads(info["d"])["files"]
                else:
                    self._file_list = info["data"]["files"]
                # print info["data"]

    def start_download(self):
        if self._file_list[0]['disk_url'].startswith('rerewrweset'):
            print "download from ilustre"
            self.download_files_v3()
        else:
            print "download from s3"
            self.s3_download_files()

    def s3_download_files(self):
        """[summary]
        下载文件
        [description]
        modified by hd 20200508 有部分项目写到前端数据库有问题，导致下载不下来，默认线上传入到s3nb，线下s3中
        """
        manager = S3TransferManager(use_db=True, bcl_type=self.mode)
        time = datetime.datetime.now()
        for f_info in self._file_list:
            fu = f_info["disk_url"]
            if fu.split(':')[0]:
                region = fu.split(':')[0]
            else:
                if self.mode in ['nsanger', 'sanger']:
                    region = 's3nb'
                else:
                    region = 's3'
            target_file = '://'.join([region, fu.split(':')[1]])
            # target_file = '://'.join([fu.split(':')[0], fu.split(':')[1]])
            manager.add(from_uri=target_file, to_uri=os.path.join(self.outpath, f_info["current_path"],
                                                                  f_info["file_name"]))
        manager.wait()
        # self.logger.info("共使用{}s所有文件下载完成!".format((datetime.datetime.now() - time).seconds))
        print "共使用{}s所有文件下载完成!".format((datetime.datetime.now() - time).seconds)

    def download_files_v3(self):
        """
        完善下下载ilustre上面的文件
        :return:
        """
        # print self._file_list
        for m in self._file_list:
            if re.search('workflow_results', m['disk_url']):
                path = os.path.dirname(m['disk_url'].split('workflow_results/')[1])
            elif re.search('interaction_results', m['disk_url']):
                path = os.path.dirname(m['disk_url'].split('interaction_results/')[1])
            else:
                path = os.path.basename(os.path.dirname(m['disk_url']))
            target_path = os.path.join(self.outpath, path)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            self.downloadonefile(os.path.join(self._basepath, m['disk_url']), target_path)

    def downloadonefile(self, file_path, output_dir):
        """
        wget http://bcl.sanger.com/pdata/rerewrweset/files/m_6868/6868_5b3991c199fce/i-sanger
        _94011/workflow_results/geneset/uniGeneset/geneCatalog_stat.xls
        :param file_path:
        :param output_dir:
        :return:
        """
        print '开始下载：{}'.format(file_path)
        for i in range(3):
            code = os.system('wget -c {} -P {}'.format(file_path, output_dir))
            if code == 0:
                print '{} 下载成功！'.format(file_path)
                break
            else:
                if i == 2:
                    print "{} 下载失败!".format(file_path)
                else:
                    print '{} 下载失败，将尝试重新下载!'.format(file_path)

    # def download_files(self):
    #     """
    #     遍历文件列表， 并下载文件
    #         "files": [
    #     {
    #         "file_name": "seqs_tax_assignments.txt",
    #         "current_path": "sanger_15004/cmd_112_1493109842/output/Tax_assign/",
    #         "disk_url": "rerewrweset/files/m_193/10007924/i-sanger_14621/cmd_112_14931098
    #         42/output/Tax_assign/seqs_tax_assignments.txt"
    #     }
    #     """
    #     total_sum = len(self._file_list)
    #     count = 1
    #     for f_info in self._file_list:
    #         file_name = os.path.basename(f_info["file_name"])
    #         dir_name = os.path.dirname(f_info["current_path"])
    #         local_dir = os.path.join(self.outpath, dir_name)
    #         local_file = os.path.join(local_dir, file_name)
    #         disk_url = self.config_path + f_info['disk_url']
    #         # biocluster接口：file_list.append([full_path, file_size, rel_path, 2])
    #         # file_name = os.path.basename(f_info[0])
    #         # dir_name = os.path.dirname(f_info[2])
    #         # local_dir = os.path.join(self.outpath, dir_name)
    #         # local_file = os.path.join(local_dir, file_name)
    #
    #         # self.logger.info("正在下载第 {}/{} 个文件: {}, 文件大小{}".format(count, total_sum, file_name, f_info[1]))
    #         self.logger.info("正在下载第 {}/{} 个文件: {}...".format(count, total_sum, file_name))
    #         count += 1
    #         # post_info = urllib.urlencode({'indentity_code': self.identity, 'file': f_info[0], 'mode': self.mode})
    #         post_info = urllib.urlencode({'file': disk_url, 'verify': "sanger-data-upanddown"})
    #         request = urllib2.Request(self.download_url, post_info)
    #         self.logger.info("request:{}".format(self.download_url))
    #         try:
    #             u = urllib2.urlopen(request)
    #             self.logger.info("{}".format(u))
    #             try:
    #                 os.makedirs(local_dir)
    #             except OSError as exc:
    #                 if exc.errno != errno.EEXIST:
    #                     raise exc
    #                 else:
    #                     pass
    #         except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException) as e:
    #             self.logger.info(e)
    #             continue
    #         meta = u.info()
    #         file_size = int(meta.getheaders("Content-Length")[0])
    #         file_size_dl = 0
    #         block_sz = 51200
    #         f = open(local_file, "wb")
    #         while True:
    #             buffer = u.read(block_sz)
    #             if not buffer:
    #                 break
    #             file_size_dl += len(buffer)
    #             f.write(buffer)
    #             status = "{:10d}  [{:.2f}%]".format(file_size_dl, file_size_dl * 100 / file_size)
    #             self.logger.info(status)
    #         f.close()
