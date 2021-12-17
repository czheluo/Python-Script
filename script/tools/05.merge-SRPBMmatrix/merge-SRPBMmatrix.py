#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
"""
根据原始counts矩阵 和 比对统计结果 ，获得srpbm矩阵表
"""
__author__ = 'caixia tian'
__date__= '2019/08/22'
import os
import argparse
import sys


parser = argparse.ArgumentParser(description="input  parameters")
parser.add_argument('-m', '--map',required=True, help=' mapping reads count file ')
parser.add_argument('-i', '--count',required=True, help=' input count matrix table ')
parser.add_argument('-o', '--srpbm',required=True, help=' ouput srpbm matrix table ')
args = parser.parse_args()

##########获取所有样本的比对上的readscount 存入字典##########
with open(args.map) as in1:
    stat={}
    for line in in1:
        if line.startswith('#') or line.startswith('sample'):
            continue
        else:
            list1 = line.strip().split('\t')
            samid = list1[0]
            mapreads = list1[1].split('/')[0]
            if samid is '':
                continue
            stat[samid]=mapreads


with open(args.count) as in2, open(args.srpbm,'w') as out1:
    samples = []
    length = ''
    for line in in2:###获得表头行信息 获取所有列对应的样本名称###
        if line.startswith('circRNA'):
            samples = line.strip().split('\t')
            length = len(samples)
            out1.write(line )
        else:###逐行处理：将count转换成srpbm###
            info = line.strip().split('\t')
            list2 = []
            for i in range(1,length):
                raw_count = info[i]
                new_srpbm = int(info[i])*1000000000 / int(stat[samples[i]])
                list2.append(str(new_srpbm))
            out1.write(info[0] + '\t' + '\t'.join(list2) + '\n')

