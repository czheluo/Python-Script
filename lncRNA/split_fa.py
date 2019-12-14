import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', help='filter3.fa', required=True)
parser.add_argument('-n', type=int, required=True, help='number of seqs for each splitting')
parser.add_argument('-o', default='split', help='prefix file name')
args = parser.parse_args()
in_file, out_file, seq_n = args.i, args.o, args.n

with open(in_file) as f:
    seq_number = 0
    file_id = 1
    f2 = open(out_file+"1.fa", 'w')
    for line in f:
        if line.startswith('>'):
            seq_number += 1
            if seq_number <= seq_n:
                f2.write(line)
            else:
                f2.close()
                file_id += 1
                f2 = open(out_file+str(file_id)+".fa", 'w')
                f2.write(line)
                seq_number = 1
        else:
            f2.write(line)
    f2.close()

