#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
"""
Computing GC Content
"""
__author__ = 'caixia tian'
__date__= '2019/08/08'

import os
import argparse
import sys
import re

parser = argparse.ArgumentParser(description="input  parameters")
parser.add_argument('-i', '--fa',required=True, help=' a fasta file ')
parser.add_argument('-o', '--out',required=True, help='ouput file name')
args = parser.parse_args()


def gc_content( s ):
    seq = s.upper()
    total = len(seq)
    count = {}
    for base in seq:
        count.setdefault(base, 0) # 方法调用确保了键存在于 count 字典中(默认值是 0)
        count[base] = count[base] + 1
    gcnum = count['G'] + count['C']
    result = "%.2f%%" %(gcnum/total * 100)
    return result

with open(args.fa) as inp:
    stat={}
    for line in inp:
        if line.startswith('>'):
            seqid=line.replace('>','').split()[0]
            stat[seqid]=''
            #print(seqid)
            #break
        else:
            stat[seqid]+=line.replace('\n','').strip()


idlist=[]
gclist=[]
for name in stat:
    #print name,'\n',stat[name],'\n',gc_content(stat[name]),'\n'
    #break
    idlist.append(name)
    gclist.append(gc_content(stat[name]))

maxgc=max(gclist)
maxindex=gclist.index(maxgc)
output=idlist[maxindex] + '\n' + maxgc + '\n'
with open(args.out,"w") as oup:
    oup.write (output)

#########################################################
"""
Input fasta
>Rosalind_6404
CCTGCGGAAGATCGGCACTAGAATAGCCAGAACCGTTTCTCTGAGGCTTCCGGCCTTCCC
TCCCACTAATAATTCTGAGG
>Rosalind_5959
CCATCGGTAGCGCATCCTTAGTCCAATTAAGTCCCTATCCAGGCGCTCCGCCGAAGGTCT
ATATCCATTTGTCAGCAGACACGC
>Rosalind_0808
CCACCCTCGTGGTATGGCTAGGCATTCAGGAACCGGAGAACGCTTCAGACCAGCCCGGAC
TGGGAACCTGCGGGCAGTAGGTGGAAT

Output result
Rosalind_0808
60.92%
"""
