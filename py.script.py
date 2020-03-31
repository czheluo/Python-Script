#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
upload files to baiducloud
"""
__author__ = 'Meng Luo'
__Email__ = 'meng.luo@majorbio.com'
__copyright__ = 'Copyright (C) 2020 MARJOBIO'
__license__ = 'GPL'
__modified__= '2020--'

from bypy import ByPy
import argparse
import time
import os
from multiprocessing import Pool
import random
import sys
reload(sys)
sys.setdefaultencoding('utf8')

parser = argparse.ArgumentParser(description="upload files to baiducloud")
parser.add_argument("-i", "--infile", type=str, help="absolute path", required=True)
parser.add_argument("-n", "--dirname", type=str, help="tagert dir name, English name for best", required=True)
args = parser.parse_args()
"""
bypy info
python uploaddatatobaiducloud -i /mnt/ilustre/centos7users/meng.luo/project/zhoulonghua_MJ20190922067/workflow_results/Result/ -n zhoulonghua

"""

def script_run(localpath, remotepath):
    print 'Run task %s (%s)...' % (os.path.basename(localpath), os.getpid())
    start = time.time()
    try:
        cmd = 'bypy upload {} /{} -v'.format(localpath, remotepath.lstrip('/'))
        os.system(cmd)
    except Exception as e:
        print 'Task %s runs failed, because of %s' % (os.path.basename(localpath), e)
    else:
        print 'Task %s runs successful' % (os.path.basename(localpath))
    end = time.time()
    print 'Task %s runs end,  %0.2f seconds.' % (os.path.basename(localpath), (end - start))


class Upload(object):
    def __init__(self, medpath, panedirname):
        self.panedirname = panedirname
        self.medpath = medpath.rstrip('/') + '/'
        self.newdir, self.filelist = '', []
        self.bp = ByPy()
    
    def run(self):
        """
        该方法是遍历文件夹中所有的文件，然后逐一进行上传
        :return:
        """
        self.get_filelist(self.medpath)
        self.bp.mkdir(remotepath=self.panedirname)
        print "文件夹{}创建成功！".format(self.panedirname)
        time.sleep(2)
        print('Parent process %s.' % os.getpid())
        p = Pool(5)
        for m in self.filelist:
            ab_path = m.split(self.medpath)[1]
            if len(ab_path.split('/')) > 1:
                localpath = os.path.join(self.medpath, ab_path)
                remotepath = os.path.join(self.panedirname, '/'.join(ab_path.split('/')[:-1]).lstrip('/'))
                self.bp.mkdir(remotepath)
            else:
                localpath = os.path.join(self.medpath, ab_path)
                remotepath = self.panedirname
            print "start upload {} to /{}".format(localpath, remotepath.lstrip('/'))
            p.apply_async(script_run, args=(localpath, remotepath,))
        print 'Waiting for all subprocesses done...'
        p.close()  # 关闭不在添加子进程
        p.join()
        print 'All subprocesses done.'

    def get_filelist(self, dir_path):
        """
        遍历文件夹中所有的文件
        :param dir_path:
        :return:
        """
        self.newdir = dir_path
        if os.path.isfile(dir_path):
            self.filelist.append(dir_path)
        elif os.path.isdir(dir_path):
            for s in os.listdir(dir_path):
                self.newdir = os.path.join(dir_path, s)
                self.get_filelist(self.newdir)


if __name__ == '__main__':
    a = Upload(args.infile, args.dirname)
    a.run()
