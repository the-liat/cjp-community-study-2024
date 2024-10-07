import os
from glob import glob
from pprint import pprint as pp
import pandas as pd


input_dir = r'C:\Users\Liat Sayfan\Documents\CJP Contact Lists'
target_dir = r'C:\Users\Liat Sayfan\Documents\CJP Contact Lists\output'
org_names_file = f'{target_dir}/org_names.txt'

def convert_files():
    os.makedirs(target_dir, exist_ok=True)
    # Read file list from target directory (*.xlsx)
    files = glob(f'{input_dir}/*.xlsx')
    for f in files[1:]:
        sheets = pd.read_excel(f, sheet_name=None)  # Returns a dictionary of DataFrames
        df = list(sheets.values())[0]   # Save each sheet as a CSV
        base_name = os.path.basename(f)
        csv_file = f'{input_dir}/output/{base_name.replace(".xlsx",".csv")}'
        if os.path.isfile(csv_file):
            continue
        print('converting:', csv_file)
        df.to_csv(csv_file, index=False)

def generate_org_list():
    files = glob(f'{input_dir}/*.xlsx')
    org_list = []
    for f in files:
        org_name = os.path.basename(f).split('.')[0]
        org_list.append(org_name)
    s = "\n".join(org_list)
    open(org_names_file, 'w').write(s)

def main():
    # convert_files()
    generate_org_list()

if __name__ == "__main__":
    main()