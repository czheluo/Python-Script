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

'''
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
			#cnc.insert(0,str(spl[1]))
			print(cnc)
			#resu= ''+str(spl[1])+' '+str(cnc)
			#print(resu)
			oup.write(cnc)

alt_map = {'ins':'0'}
complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'} 

def reverse_complement(seq):    
    for k,v in alt_map.iteritems():
        seq = seq.replace(k,v)
    bases = list(seq) 
    bases = reversed([complement.get(base,base) for base in bases])
    bases = ''.join(bases)
    for k,v in alt_map.iteritems():
        bases = bases.replace(v,k)
    return bases

>>> seq = "TCGGinsGCCC"
>>> print "Reverse Complement:"
>>> print(reverse_complement(seq))
GGGCinsCCGA
'''

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

