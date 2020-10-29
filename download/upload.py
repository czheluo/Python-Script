#!/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'yuguo'
# last modified by hongdong@20181016


import argparse
import os
from libs.upload_task import UploadTask
from get_file_list import get_list


parser = argparse.ArgumentParser(description="根据验证码，上传一个文件夹至某一个项目下")
parser.add_argument("-i", "--input_dir", help="输入的文件夹的路径", required=True)
parser.add_argument("-l", "--file_list", help="文件列表名字,不存在则根据input_dir自动生成, 用于描述文件的信息, "
                                              "其表头必须为文件路径、文件大小、文件描述、是否锁定，"
                                              "锁定文件不允许客户类型用户下载", required=True)
parser.add_argument("-p", "--project_type", help="输入项目类型，如dna_gmap.gmap")

parser.add_argument("-c", "--identity_code", help="验证码,上传时必须提供", default="none")
parser.add_argument("-s", "--silence", help="静默模式，当把该值设为T时, 将不再在屏幕上输出日志信息"
                                            "，默认为T", default="T")
parser.add_argument("-m", "--mode", help="模式, 为nsanger, sanger、tsanger、tsg中的一个， "
                                         "默认为nsanger", default="nsanger")
parser.add_argument("-f", "--fake", help="只发送文件路径，实际不传文件,只限于有磁盘访问权限的开发人员或管理员使用该参数，"
                                         "需另外拷贝文件到目标路径", default="False")
parser.add_argument("-npf", "--is_new_platform", help="是否是创新平台，默认不是创新平台", default="False")
args = vars(parser.parse_args())

if not os.path.exists(args["input_dir"]):
    raise OSError("输入路径 {} 不存在".format(args["input_dir"]))

if os.path.isfile(args["input_dir"]):
    raise OSError("输入路径不能为文件，只能为文件夹")

if not os.path.exists(args["file_list"]):
    print("list文件{}不存在，使用输入目录{}生成list文件".format(args["file_list"], args["input_dir"]))
    get_list(args["input_dir"], args["file_list"])

if args["identity_code"] == "none":
    raise ValueError("验证码不能为none")

if args["silence"] not in ["T", "F"]:
    raise ValueError("参数-s的值必须是T或者是F")

if args["mode"] not in ["sanger", "tsanger", "tsg", "sg", "nsanger"]:
    raise ValueError("参数-m的值必须是sanger或者是tsanger,tsg,nsanger")

if args["silence"] == "F":
    stream_on = True
else:
    stream_on = False
if args["project_type"]:
    project_type = args["project_type"]
else:
    project_type = None
is_new_platform = False
if args['is_new_platform'] in ["True", "T", "true"]:
    is_new_platform = True
task = UploadTask(os.path.abspath(args["input_dir"]), os.path.abspath(args["file_list"]), args["identity_code"],
                  args["mode"], stream_on, project_type, is_new_platform)

if args["fake"] == "False":
    task.s3_upload_files()
task.post_filesdata()
