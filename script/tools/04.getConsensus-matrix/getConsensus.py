#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
get Consensus and base number matrix
"""
__author__ = 'caixia tian'
__date__= '2019/08/15'

import os
import argparse
import sys
from collections import Counter

parser = argparse.ArgumentParser(description="input  parameters")
parser.add_argument('-i', '--input',required=True, help=' a fasta file ')
parser.add_argument('-o', '--output',required=True, help=' ouput result file ')
args = parser.parse_args()

#############处理输入文件，获得需要处理的所有序列#############
with open(args.input) as inp:
    stat={}
    testid=''
    for line in inp:
        if line.startswith('>'):
            seqid=line.replace('>','').split()[0]
            stat[seqid]=''
            if testid is '':
                testid = seqid
        else:
            info = line.upper()
            stat[seqid]+=info.replace('\n','').strip()

    seq_len = len(stat[testid])

####定义一个函数，采用列表计数法来计算多个序列的Consensus#####
def getConsensus(seqs):
    A,T,C,G = [],[],[],[]
    consensus = ''
    for i in range(seq_len):
        seq = ''
        for n in seqs.keys():
            seq += seqs[n][i]
        A.append(seq.count('A'))
        T.append(seq.count('T'))
        C.append(seq.count('C'))
        G.append(seq.count('G'))
        counts = Counter(seq) #Counter({'A':5, 'T':1, 'G':1, 'C':0})
        consensus += counts.most_common()[0][0]#取出计数最大的元素的键
    result = 'consensus:\t' + consensus + '\n'
    result += '\n'.join(['A:\t'+' '.join(map(str,A)), 'T:\t'+' '.join(map(str,T)), 'C:\t'+' '.join(map(str,C)),'G:\t'+' '.join(map(str,G))]) + '\n'
    #' '.join(map(str,A))  把 list [5, 1, 0, 0, 5, 5, 0, 0] 格式转化成 5 1 0 0 5 5 0 0
    return result

###################调用函数，计算并输出#######################

oup = open(args.output,"w")
oup.write(getConsensus(stat))
oup.close()
########################输入和输出示例########################
"""INPUT
>Rosalind_1
ATCCAGCT
>Rosalind_2
GGGCAACT
>Rosalind_3
ATGGATCT
>Rosalind_4
AAGCAACC
>Rosalind_5
TTGGAACT
>Rosalind_6
ATGCCATT
>Rosalind_7
ATGGCACT

OUTPUT
consensus:  ATGCAACT
A:  5 1 0 0 5 5 0 0
T:  1 5 0 0 0 1 1 6
C:  0 0 1 4 2 0 6 1
G:  1 1 6 3 0 1 0 0
"""
