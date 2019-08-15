#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Consensus and Profile
"""
__author__ = 'Meng Luo'
__Email__ = 'meng.luo@majorbio.com'
__copyright__ = 'Copyright (C) 2019 MARJOBIO'
__license__ = 'GPL'
__modified__= '20190815'

import os
import argparse
import sys
import re

parser = argparse.ArgumentParser(description="input  parameters")
parser.add_argument('-i', '--fa',required=True, help=' a fasta file ')
parser.add_argument('-o', '--out',required=True, help='ouput file name')
args = parser.parse_args()
'''
python cons.py -i file.fa -o file.result
'''

def famat(seq):
	seqmat = []
	hd=[]
	for line in seq:
		if re.match(">", line):
			spl=line.split(">")
			hd.append(spl)
		else:
			seqmat.append(line.rstrip())
	#mat='\n'.join(seqmat)
	#hds=''.join(hd)
	return "\n".join(seqmat)

def profile(matrix):
    strings = matrix.split()
    default = [0] * len(strings[0])
    results = {
        'A': default[:],
        'C': default[:],
        'G': default[:],
        'T': default[:],
    }
    for s in strings:
        for i, c in enumerate(s):
            results[c][i] += 1
    return results

def consensus(profile):
    result = []
    resu= []
    keys = profile.keys()
    for j in keys:
        res=j + ":" + " ".join(str(x) for x in profile[j])
        resu.append(res)
    for i in range(len(profile[keys[0]])):
        max_v = 0
        max_k = None
        for k in keys:
            v = profile[k][i]
            if v > max_v:
                max_v = v
                max_k = k
        result.append(max_k)
    resuls=''.join(result)+'\n'+'\n'.join(resu)
    return resuls

dataset = open(args.fa,"r")
out = open(args.out,"w")
ma = famat(dataset)
pro = profile(ma)
cp = consensus(pro)
out.write(cp)

# show result

'''

ATGCAACT
A:5 1 0 0 5 5 0 0
C:0 0 1 4 2 0 6 1
T:1 5 0 0 0 1 1 6
G:1 1 6 3 0 1 0 0
'''