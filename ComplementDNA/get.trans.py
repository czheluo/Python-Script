#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complementing a Strand of DNA
"""
__author__ = 'Meng Luo'
__Email__ = 'meng.luo@majorbio.com'
__copyright__ = 'Copyright (C) 2019 MARJOBIO'
__license__ = 'GPL'
__modified__= '20190801'

import os
import argparse
import sys
import re

parser = argparse.ArgumentParser(description="input  parameters")
parser.add_argument('-i', '--fa',required=True, help=' a fasta file ')
parser.add_argument('-o', '--out',required=True, help='ouput file name')
args = parser.parse_args()

def Reverse(seq):
    rev = []
    x = len(seq)
    for i in seq:
        x = x - 1
        rev.append(seq[x])
    return ''.join(rev)

def complement(RC):
    comp = []
    for i in RC:
        if i == "T":
            comp.append("A")
        if i == "A":
            comp.append("T")
        if i == "G":
            comp.append("C")
        if i == "C":
            comp.append("G")
    return ''.join(comp)

with open(args.fa) as inp,open(args.out,"w") as oup:
	for line in inp:
		if re.match(">", line):
			spl=line.split(">")
			#spn=spl.rstrip()
		else:
			rc = Reverse(line)
			rcc = complement(rc)
			resu = str(spl[1].rstrip())+'	'+str(rcc)+'\n'
			oup.write(resu)

