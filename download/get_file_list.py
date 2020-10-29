#!/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'xuting'
# modified by yuguo at 20170920
from __future__ import division
import argparse
import os
import re


def get_size(path, unit='B'):
    """
    获取文件大小
    """
    b = os.path.getsize(path)
    if unit == 'B':
        return "{}B".format(b)
    else:
        if b / 1024 < 1:
            return "{}B".format(b)
        elif b >= 1024 and b < 1024 * 1024:
            return "{:.3f}KB".format(b / 1024)
        elif b >= 1024 * 1024 and b < 1024 * 1024 * 1024:
            return "{:.3f}MB".format(b / (1024 * 1024))
        else:
            return "{:.3f}GB".format(b / (1024 * 1024 * 1024))


def get_list(source_dir, list_path):
    source_dir = os.path.abspath(source_dir)
    list_path = os.path.abspath(list_path)
    file_list = list()

    # if not os.path.isabs(source_dir):
    #     raise Exception("{} 不是一个绝对路径".format(source_dir))

    if not os.path.isdir(source_dir):
        raise Exception("{} 文件夹不存在或者不是一个合法的文件夹".format(source_dir))

    try:
        with open(list_path, "wb") as w:
            # w.write("#source#{}\n".format(source_dir))
            w.write("{}\t{}\t{}\t{}\n".format("文件路径", "文件大小", "文件描述", "是否锁定"))
    except Exception as e:
        raise Exception(e)

    for d in os.walk(source_dir):
        for f in d[2]:
            full_path = os.path.join(d[0], f)
            file_size = get_size(full_path, unit='B')
            file_list.append([full_path, file_size])

    with open(list_path, "ab") as a:
        for l in file_list:
            locked = "0"
            fq_pattern = '(fq$)|(fastq$)|(fq.gz$)|(fastq.gz$)|(fq.tgz$)|(fastq.tgz$)|(fq.rar$)|(fastq.rar$)|(fq.zip$)' \
                         '|(fastq.zip$)'
            fa_pattern = '(fa$)|(fasta$)|(fa.gz$)|(fasta.gz$)|(fa.tgz$)|(fasta.tgz$)|(fa.rar$)|(fasta.rar$)|(fa.zip$)' \
                         '|(fasta.zip$)'
            if re.search(fq_pattern, os.path.basename(l[0])) or re.search(fa_pattern, os.path.basename(l[0])):
                locked = "1"
            a.write("{}\t{}\t{}\t{}\n".format(l[0], l[1], "", locked))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="根据提供的路径, 解析该路径的目录结构")
    parser.add_argument("-i", "--input", help="输入的文件的路径", required=True)
    parser.add_argument("-l", "--list", help="生成list文件名", required=True)
    args = vars(parser.parse_args())
    get_list(args["input"], args["list"])
