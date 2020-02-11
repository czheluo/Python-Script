#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
model script

"""
__author__ = 'Meng Luo'
__Email__ = 'meng.luo@majorbio.com'
__copyright__ = 'Copyright (C) 2019 MARJOBIO'
__license__ = 'GPL'
__modified__= '20190808'

"""
Script:

Description:

Example:


Usage: popgenome.py -v <vcf> [-d <dir>] [-T] [-F] [POPLIST ...] [-w <window>] [-s <step>] [-t <type>] [-g <outgroup>]

Options:
  -v <vcf>  Directory containing vcf files
  -d <dir>  Path of analysis output files [default: ./]
  -T  Testing neutrality including TajimaD
  -F  Calculating Fst and Pi
  POPLIST  Files in .csv format each containing the individuals of one population in one column
  -w <window>  Sliding window
  -s <step>  Step for window
  -t <type>  Sliding type: type=1 for SNP and type=2 for genomic region
  -g <outgroup>  Set outgroup
  --version  Show version
  -h --help
"""

from docopt import docopt
import sys,re,os,time



if __name__ =="__main__":
        arguments = docopt(__doc__,version='popgenome_v1.0')

print(arguments)
print("\n\n")

# start timing 
start=time.asctime()


end=time.asctime()
print("\nOver!\n")
print ("start time: %s\n" % (start))
print("end time: %s\n" % (end))
