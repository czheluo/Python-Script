#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GC content
"""
__author__ = 'Meng Luo'
__Email__ = 'meng.luo@majorbio.com'
__copyright__ = 'Copyright (C) 2019 MARJOBIO'
__license__ = 'GPL'
__modified__= '20190808'

import os
import argparse
import sys
import re

parser = argparse.ArgumentParser(description="input  parameters")
parser.add_argument('-i', '--fa',required=True, help=' a fasta file ')
parser.add_argument('-o', '--out',required=True, help='ouput file name')
args = parser.parse_args()
'''
python gc.content.py -i file.fa -o file.result
'''

def gccontent(seq):
    a = 0
    g = 0
    c = 0
    t = 0
    for i in seq:
        if i == "T" or i == "t":
            t += 1
        if i == "A" or i == "a":
            a += 1
        if i == "G" or i == "g":
            g += 1
        if i == "C" or i == "c":
            c += 1
    return (g+c)*100/(a+g+c+t)

with open(args.fa) as inp,open(args.out,"w") as oup:
	resu1 = 'sample name'+'\t'+'GC%'+'\n'
	oup.write(resu1)
	for line in inp:
		if re.match(">", line):
			spl=line.split(">")
			#spn=spl.rstrip()
		else:
			gcc = gccontent(line)
			resu2 =str(spl[1].rstrip())+'\t'+str(gcc)+'%'+'\n'
			oup.write(resu2)

