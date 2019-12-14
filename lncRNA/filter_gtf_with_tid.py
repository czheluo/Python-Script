import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-g', required=True, help='strtie merged gtf')
parser.add_argument('-t', required=True, help='transcript list')
parser.add_argument('-o', required=True, help='ouput file name')
parser.add_argument('-v', help='invert-match mode', default=False, action='store_true')
args = parser.parse_args()

def parse_gtf_col9(col9):
    tmp_list = col9.strip('\n').strip(";").split(";")
    tmp_dict = dict()
    for each in tmp_list:
        name, value = each.split()
        name = name.strip()
        value = value.strip().strip('"')
        tmp_dict[name] = value
    return tmp_dict

transcript_list = [x.strip().split()[0] for x in open(args.t) if x]
with open(args.g) as f, open(args.o, 'w') as f2:
    for line in f:
        if line.startswith('#'):
            continue
        col9 = line.strip().split('\t')[8]
        col9_dict = parse_gtf_col9(col9)
        if not col9_dict['transcript_id'] in transcript_list:
	    if args.v:
		f2.write(line)
	else:
	    if not args.v:
		f2.write(line)


