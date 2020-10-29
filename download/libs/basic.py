# -*- coding: utf-8 -*-
# __author__ = 'xuting'
# modified by yuguo at 20170920
# lasted modified by hd@20200820 增加新的验证信息

import getpass
import socket
from logger import Wlog
# import json
# from datetime import datetime, date


class Basic(object):
    def __init__(self, outdir, identity, mode, stream_on):
        self._identity = identity
        self._stream_on = stream_on
        # self._port = port
        self._mode = mode
        self._ip = ""
        self._user = ""
        # self._url = self.get_url(mode, port)
        self.get_ip()
        self.get_user()
        self._file_list = list()
        self.outdir = outdir
        self.logger = Wlog(self).get_logger("")

        self.prefix_path = ""  # sanger:  or tsanger:
        self.config_path = ""  # /mnt/iusture/data
        self.client = ""
        self.client_key = ""
        self.post_url = ""
        self.post_add_url = ""
        self.upload_url = "http://192.168.12.101/tsgupload.php"
        self.download_url = "http://192.168.12.101/tsgdownload.php"
        if mode == "tsanger" or mode == "tsg" or mode == "sg":
            self.prefix_path = "tsanger:"
            self.config_path = "/mnt/ilustre/tsanger-data/"
            self.client = "client03"
            self.client_key = "hM4uZcGs9d"
            self.post_url = "http://api.{}.com/file/verify_filecode".format(mode)
            self.post_add_url = "http://api.{}.com/file/add_file_by_code".format(mode)
            self.post_url_n = "http://apicenter.nsg.com/index/in"
            # 验证验证码，并返回路径或者文件路径等信息
            self.binds_id = "5f3db4c89b79000093007f89"
            self.interface_id = 39
            self.env_name = "offline"
            self.key = "548ea91e41152bca9125076a0c4cd52b"
            # 向前端请求发送文件信息到他们mysql中
            self.binds_id_add = "5f3db4859b79000093007f86"
            self.interface_id_add = 30
            self.key_add = "548ea91e41152bca9125076a0c4cd52b"
        elif mode == "sanger":
            # mode = "test_sanger"
            self.config_path = "/mnt/ilustre/data/"
            self.prefix_path = "sanger:"
            self.client = "client01"
            self.client_key = "1ZYw71APsQ"
            self.post_url = "http://api.{}.com/file/verify_filecode".format(mode)
            self.post_add_url = "http://api.{}.com/file/add_file_by_code".format(mode)
            self.post_url_n = "http://apicenter.lab.majorbio.com/index/in"
            # 验证验证码，并返回路径或者文件路径等信息
            self.binds_id = "5f3db4c89b79000093007f89"
            self.interface_id = 39
            self.env_name = "online"
            self.key = "03225b8301ff8a32605e25a4566a4170"
            # 向前端请求发送文件信息到他们mysql中
            self.binds_id_add = "5f3db4859b79000093007f86"
            self.interface_id_add = 30
            self.key_add = "03225b8301ff8a32605e25a4566a4170"
        elif mode == 'nsanger':
            self.config_path = "/mnt/ilustre/data/"
            self.prefix_path = "nsanger:"
            self.client = "client01"
            self.client_key = "1ZYw71APsQ"
            self.post_url = "http://api.sanger.com/file/verify_filecode".format(mode)
            self.post_add_url = "http://api.sanger.com/file/add_file_by_code".format(mode)
            self.post_url_n = "http://apicenter.lab.majorbio.com/index/in"
            # 验证验证码，并返回路径或者文件路径等信息
            self.binds_id = "5f3db4c89b79000093007f89"
            self.interface_id = 39
            self.env_name = "online"
            self.key = "03225b8301ff8a32605e25a4566a4170"
            # 向前端请求发送文件信息到他们mysql中
            self.binds_id_add = "5f3db4859b79000093007f86"
            self.interface_id_add = 30
            self.key_add = "03225b8301ff8a32605e25a4566a4170"

    @property
    def user(self):
        return self._user

    # @property
    # def url(self):
    #     return self._url

    @property
    def ip(self):
        return self._ip

    @property
    def identity(self):
        return self._identity

    # @property
    # def target_path(self):
    #     return self._target_path

    @property
    def stream_on(self):
        return self._stream_on

    # @property
    # def port(self):
    #     return self._port

    @property
    def mode(self):
        return self._mode

    def get_ip(self):
        """
        获取客户端的ip
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("baidu.com", 80))
        self._ip = s.getsockname()[0]
        s.close()
        return self._ip

    def get_user(self):
        self._user = getpass.getuser()
        return self._user

    def get_url(self, mode, port):
        """
        获取服务器端的ip，需要在子类中进行重写
        """
        pass
