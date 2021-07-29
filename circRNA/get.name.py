#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GC content
"""
__author__ = 'Meng Luo'
__Email__ = 'meng.luo@majorbio.com'
__copyright__ = 'Copyright (C) 2021 MARJOBIO'
__license__ = 'GPL'
__modified__= '20210728'

import os
import argparse
import sys
import re

parser = argparse.ArgumentParser(description="input  parameters")
parser.add_argument('-i', '--fa',required=True, help=' a fasta file ')
parser.add_argument('-o', '--org',required=True, help='org file name')
args = parser.parse_args()
'''
python get.name.py -i mature.fa -o Arabidopsis
 
'''

with open(args.fa) as fa:
	#resu1 = 'sample name'+'\t'+'GC%'+'\n'
	#oup.write(resu1)
    out=open('mature_'+str(args.org)+'.dna.fa',"w")
    for line in fa:
        if re.match(">", line):
            spll=line.replace(">","")
            spls=spll.split(" ")
                    #print(spls[2].rstrip())
			#spn=spl.rstrip()
        else:
            lines=line.replace("U", "T")
            #resu=spls[2].rstrip()+' '+spls[3].rstrip()+'\t'+spl[2].rstrip()+'\n'     
                    #print(resu)
                    #sp=spl[2].split(" ")
            if spls[2].rstrip() == args.org:
                resu2 ='>'+str(spls[0].rstrip())+'\n'+str(lines.rstrip())+'\n'
                print(resu2)
                out.write(resu2)
