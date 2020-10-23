from __future__ import print_function
import subprocess
from multiprocessing import Pool
import argparse
import shlex
import os


def hisat2(tuple_arg):
    """
    using hisat2 with default essential parameters for pair-end data
    :param tuple_arg:
    :return:
    """
    samtools = '/mnt/ilustre/users/deqing.gu/software/samtools-1.3.1/samtools'
    # unpack args
    sample, r1, r2, x, p, s = tuple_arg
    # create output dir
    subprocess.call('mkdir {sample}'.format(sample=sample), shell=True)
    # using hisat2
    if s == 'RF':
	s = '--rna-strandness RF'
    elif s == 'FR':
        s = '--rna-strandness FR'
    else:
	s = ''
	print('No strandness was set')
	
    hisat = 'hisat2 -x {x} -p {p} -1 {r1} -2 {r2} ' \
            '{strand} ' \
            '--un-conc-gz {sample}/{sample}.unmapped.gz ' \
            '--novel-splicesite-outfile {sample}/splice.bed ' \
            '-S {sample}/{sample}.sam ' \
            '--dta'
    hisat = hisat.format(x=x, r1=r1, r2=r2, sample=sample, strand=s, p=p)
    print(hisat)
    cmd = shlex.split(hisat)
    p = subprocess.Popen(args=cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    f = open(sample + '.hisat2.log', 'w+')
    f.write(stdout)
    f.write(stderr)
    parse_hisat2_log(f, sample)
    # convert sam file into bam file
    cmd = '{samtools} view -b -o {sample}/{sample}.bam {sample}/{sample}.sam'.format(samtools=samtools, sample=sample)
    cmd_args = shlex.split(cmd)
    subprocess.call(args=cmd_args)
    # remove sam files
    subprocess.Popen('rm {sample}/{sample}.sam'.format(sample=sample), shell=True)
    # sort bam files
    cmd = '{samtools} sort -m 1G -o {sample}/{sample}.sorted.bam {sample}/{sample}.bam'.format(samtools=samtools, sample=sample)
    cmd_args = shlex.split(cmd)
    subprocess.call(args=cmd_args)
    # remove unsorted bam file
    subprocess.call('rm {sample}/{sample}.bam'.format(sample=sample), shell=True)
    # create index for sorted bam file
    cmd = '{samtools} index {sample}/{sample}.sorted.bam'.format(samtools=samtools, sample=sample)
    cmd_args = shlex.split(cmd)
    subprocess.call(args=cmd_args)

def parse_hisat2_log(f, sample):
    f.seek(0, 0)
    align = 0
    total_reads = 1
    for line in f:
        if 'reads; of these:' in line:
            total_reads = int(line.split()[0])*2
        elif 'aligned concordantly exactly 1 time' in line:
            align = align + int(line.split()[0])*2
        elif 'aligned concordantly >1 times' in line:
            align = align + int(line.split()[0])*2
        elif 'aligned discordantly 1 time' in line:
            align = align + int(line.split()[0])*2
        elif 'aligned exactly 1 time' in line:
            align = align + int(line.split()[0])
        elif 'aligned >1 times' in line:
            align = align + int(line.split()[0])
        else:
            pass
    else:
        f.close()
    map_rate = float(align)/total_reads*100
    stat_line = '{}\t{}/{}\t{:.2f}%\n'.format(sample, align, total_reads, map_rate)
    open(sample + '.align_stat', 'w').write(stat_line)


def parse_args():
    # define and parse arguments
    help_info = 'python histat2.py ref_index trimmedPair.list -p 1'
    parser = argparse.ArgumentParser(usage=help_info)
    parser.add_argument('ref_index', help='The basename of the index for the reference genome.')
    parser.add_argument('data_list', help='data file (trimPairFq.list) with each line likes: sample PE r1_path r2_path')
    parser.add_argument('-p', default=1, type=int, help='Threads number for hisat2')
    parser.add_argument('-s', default='', type=str, help='fr-firststrand corresponds to RF; fr-secondstrand corresponds to FR')
    parser.add_argument('-pool_size', default=6, type=int, help='process number.Default: 6')
    args = parser.parse_args()
    # further args parse
    ref_index = args.ref_index
    if os.path.isfile(ref_index):
        ref_path = os.path.dirname(ref_index)
        new_ref_index = os.path.join(ref_path, 'ref_index')
        cmd = 'hisat2-build {f} {index} -p 6'.format(f=ref_index, index=new_ref_index)
        ref_index = new_ref_index
        subprocess.call(cmd, shell=True)

    trimmed_data = args.data_list
    p, s, pool_size = args.p, args.s, args.pool_size
    # parse trimmed_data file
    with open(trimmed_data) as f:
        tuple_args = []
        for line in f:
            tmp = line.strip().split()
            if line:
                tuple_args.append((tmp[0], tmp[2], tmp[3], ref_index, p, s))
    return tuple_args, pool_size


def main():
    args, pool_size = parse_args()
    pool = Pool(pool_size)
    pool.map(hisat2, args)
    pool.close()
    pool.join()
    print('All subprocess for hisat2 mapping were done.')
    subprocess.call('cat *align_stat > align_stat.txt', shell=True)
    subprocess.call("find $PWD -name '*.sorted.bam' | awk -F '/' -v OFS='\t' '{print $(NF-1),$0}' > bam.list", shell=True)


if __name__ == '__main__':
    main()
