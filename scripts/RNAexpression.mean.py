#/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys

in_f = sys.argv[1]

with open(in_f, 'r') as f1:
    f_all = f1.readlines()
    f_pheno = f_all[1:]
    head = f_all[0].strip().split()
    f = open('new_' + sys.argv[1], 'w')
    j = 0
    f.writelines('sample' + '\t')
    while j < len(head):
        sample = head[j].split('_')[0]
        j += 5
        if j < len(head):
            f.writelines(sample + '\t')
        else:
            f.writelines(sample + '\n')

    for line in f_pheno:
        new_line = line.strip().split()
        name = new_line[0]
        f.writelines(name + '\t')
        i = 1
        while i < len(new_line):
            value1 = float(new_line[i])
            value2 = float(new_line[i+1])
            value3 = float(new_line[i+2])
            value4 = float(new_line[i+3])
            value5 = float(new_line[i+4])
            mean = (value1+value2+value3+value4+value5)/5
            if i+5 == len(new_line):
                f.writelines('%.2f'%mean + '\n')
            else:
                f.writelines('%.2f'%mean + '\t')
            i += 5
    f.close()

