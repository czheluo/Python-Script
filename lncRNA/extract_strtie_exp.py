import os
from glob import glob
import argparse
from math import ceil
from collections import defaultdict

def expression_from_gtf(gtf, g2tdict=dict(), sep='\t', read_len=290):
    with open(gtf) as f:
        transcript_fpkm_dict = defaultdict(list)
        transcript_tpm_dict = defaultdict(list)
        gene_fpkm_dict = defaultdict(list)
        gene_tpm_dict = defaultdict(list)
        gene2exon_dict = defaultdict(list)
        transcript2exon_dict = defaultdict(list)
        for line in f:
            if line.startswith("#"):
                continue
            if not line.strip():
                continue
            line_list = line.strip('\n').split(sep)
            if len(line_list) < 9:
                print("Line with less than 9 column and will be skipped: ", line)
                continue
            if line_list[2] == 'transcript':
                col9_dict = parse_gtf_col9(line_list[8])
                if 'FPKM' in col9_dict:
                    transcript_id = col9_dict['transcript_id']
                    gene_id = col9_dict['gene_id']
                    if ("ref_gene_name" in col9_dict) or ("gene_name" in col9_dict):
			if transcript_id in g2tdict: 
                            gene_id = g2tdict[transcript_id]
                    transcript_fpkm = float(col9_dict['FPKM'])
                    transcript_tpm = float(col9_dict['TPM'])
                    transcript_fpkm_dict[transcript_id].append(transcript_fpkm)
                    transcript_tpm_dict[transcript_id].append(transcript_tpm)
                    gene_fpkm_dict[gene_id].append(transcript_fpkm)
                    gene_tpm_dict[gene_id].append(transcript_tpm)
            elif line_list[2] == 'exon':
                col9_dict = parse_gtf_col9(line_list[8])
                transcript_id = col9_dict['transcript_id']
                gene_id = col9_dict['gene_id']
                if ("ref_gene_name" in col9_dict) or ("gene_name" in col9_dict):
		    if transcript_id in g2tdict:
                        gene_id = g2tdict[transcript_id]
                coor = [float(x) for x in  line_list[3:5]]
                start, end = min(coor), max(coor)
                exon_cov = float(col9_dict['cov'])
                exon_count = (end-start+1)*exon_cov/read_len
                gene2exon_dict[gene_id].append(exon_count)
                transcript2exon_dict[transcript_id].append(exon_count)

    return transcript_fpkm_dict, transcript_tpm_dict, gene_fpkm_dict, gene_tpm_dict, gene2exon_dict, transcript2exon_dict


def parse_gtf_col9(col9):
    tmp_list = col9.strip('\n').strip(";").split(";")
    tmp_dict = dict()
    for each in tmp_list:
        name, value = each.split('"')[0:2]
        name = name.strip()
        value = value.strip()
        tmp_dict[name] = value
    return tmp_dict


def expression2table(exp_dict_list, out_name, sep='\t', exp_type='float'):
    """ exp_dict_list example: [(sampleA, gene_fpkm_dict), ...]"""
    exp_dicts = [x[1] for x in exp_dict_list]
    samples = [x[0] for x in exp_dict_list]
    keys = set()
    for d in exp_dicts:
        keys.update(d.keys())

    with open(out_name, 'w') as f:
        header_list = ['seq_id'] + samples
        f.write(sep.join(header_list)+'\n')
        for k in keys:
            exp_list = list()
            for d in exp_dicts:
                if k in d:
		    if exp_type == 'float':
                        exp_list.append(str(sum(d[k])))
		    else:
			exp_list.append(str(ceil(sum(d[k]))))
                else:
                    exp_list.append('0')
            line_list = [k] + exp_list
            f.write(sep.join(line_list) + '\n')

# input args
parser = argparse.ArgumentParser()
parser.add_argument('-i', required=True, type=str, help='stringtie output directory')
parser.add_argument('-g2t', type=str, help='file with two column, gene -> transcript')
parser.add_argument('-l', metavar='LengthOfRead', type=int, default=290, help='Average read length. Default: 290')
args = parser.parse_args()
# get file info
os.chdir(args.i)
files = glob(r'*/*.gtf')
gtf_files = sorted([x for x in files if 'fully_covered' not in x])
# transcript-->gene_id
if args.g2t:
    g2t_dict = dict([x.strip().split()[::-1] for x in open(args.g2t) if x])
else:
    g2t_dict = dict()
#
transcript_fpkm_dict_list = list()
transcript_tpm_dict_list = list()
gene_fpkm_dict_list = list()
gene_tpm_dict_list = list()
transcript2exon_dict_list = list()
gene2exon_dict_list = list()
for gtf in gtf_files:
    sample_name = gtf.split('/')[0]
    transcript_fpkm_dict, transcript_tpm_dict, gene_fpkm_dict, gene_tpm_dict, gene2exon_dict, transcript2exon_dict = expression_from_gtf(gtf, g2t_dict, sep='\t', read_len=args.l)
    transcript_fpkm_dict_list.append((sample_name, transcript_fpkm_dict))
    transcript_tpm_dict_list.append((sample_name, transcript_tpm_dict))
    gene_fpkm_dict_list.append((sample_name, gene_fpkm_dict))
    gene_tpm_dict_list.append((sample_name, gene_tpm_dict))
    transcript2exon_dict_list.append((sample_name, transcript2exon_dict))
    gene2exon_dict_list.append((sample_name, gene2exon_dict))
# generate_table
expression2table(transcript_fpkm_dict_list, 'transcript_fpkm.xls')
expression2table(transcript_tpm_dict_list, 'transcript_tpm.xls')
expression2table(gene_fpkm_dict_list, 'gene_fpkm.xls')
expression2table(gene_tpm_dict_list, 'gene_tpm.xls')
expression2table(transcript2exon_dict_list, 'transcript_count.xls', exp_type='count')
expression2table(gene2exon_dict_list, 'gene_count.xls', exp_type='count')

