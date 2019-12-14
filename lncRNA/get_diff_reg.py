import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('-i', type=str, required=True, nargs='+', help='*diff.exp.xls')
args = parser.parse_args()

files = args.i 
for table in files:
    t = pd.read_table(table, index_col=0, header=0)
    for col in t.columns:
        if col.startswith('logFC'):
            fc_col = col
            break
    ft = t.loc[:,[fc_col, 'regulate']]
    ft.to_csv('new'+table, sep='\t')

