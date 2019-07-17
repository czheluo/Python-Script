#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
crispr pipeline
"""
__author__ = 'Meng Luo'
__Email__ = 'meng.luo@majorbio.com'
__copyright__ = 'Copyright (C) 2019 MARJOBIO'
__license__ = 'GPL'
__modified__= '20190717'

import os
import argparse
import sys
import re

parser = argparse.ArgumentParser(description="input  parameters")
parser.add_argument('-i', '--fa',required=True, help=' a fasta file ')
parser.add_argument('-o', '--out',required=True, help='ouput file name')
args = parser.parse_args()

if not args.fa:
	strs="python get.count.py --fa file.fa --out get.count"
	print(strs)
	stop

def countnc( s ):
  nc = { 'A': 0 , 'C': 0 , 'G': 0 , 'T': 0 }
  for base in s:
    if nc.has_key(base):
      nc[base] += 1
  res = ''+ str(nc['A'])+ ' '+ str(nc['C'])+ ' '+ str(nc['G'])+ ' '+ str(nc['T'])
  #print res
  return res
with open(args.fa) as inp,open(args.out,"w") as oup:
	for line in inp:
		#print(line)
		#break
		if re.match(">", line):
			spl=line.split(">")
			#print(spl[1])
			#break
		else:
			cnc=countnc(line)
			#print(cnc)
			resu= ''+str(spl[1])+' '+str(cnc)
			#print(resu)
			oup.write(cnc)





