from datetime import datetime
import json
import os
import time
from collections import defaultdict
from glob import glob
from pprint import pprint as pp
import pandas as pd
import usaddress
from config import (
    col_list,
    input_dir,
    target_dir,
    org_names_file,
    valid_orgs_file,
    all_people_json,
    all_people_csv,
    duplicates_json,
    key_separator
)


def convert_files():
    os.makedirs(target_dir, exist_ok=True)
    # Read file list from target directory (*.xlsx)
    files = glob(f'{input_dir}/*.xlsx')
    for f in files[1:]:
        sheets = pd.read_excel(f, sheet_name=None)  # Returns a dictionary of DataFrames
        df = list(sheets.values())[0]  # Save each sheet as a CSV
        base_name = os.path.basename(f)
        csv_file = f'{input_dir}/output/{base_name.replace(".xlsx", ".csv")}'
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


def merge_files():
    """Merge all files where each row contains all the personal details for each person and
      which organization lists that person appeared on (marked as 0=not on that org list or 1=yes on
      that org list.
    """
    min_col_set = {'First Name', 'Last Name'}
    orgs = open(org_names_file).read().split('\n')

    all_people = defaultdict(list)
    valid_orgs = []
    for org in orgs:
        df = pd.read_csv(f'{input_dir}/output/{org}.csv').fillna('').astype(str)
        if not min_col_set.issubset(set(df.columns)):
            continue

        print('Processing org:', org)
        valid_orgs.append(org)
        for index, row in df.iterrows():
            key = key_separator.join(row.get(col, '') for col in col_list)
            all_people[key].append(org)

    open(valid_orgs_file, 'w').write("\n".join(valid_orgs))
    json.dump(all_people, open(all_people_json, 'w'))


def generate_output_file():
    """ Create a DataFrame from the dictionary where the columns the details of a person + all org
        names and the values are 0 or 1 depending on whether the person is on that org list
    """
    all_people = json.load(open(all_people_json))
    valid_orgs = open(org_names_file).read().split('\n')
    cols = col_list + valid_orgs + ['Total Orgs']
    df = pd.DataFrame(columns=cols)
    total_people = len(all_people)
    for i, (k, v) in enumerate(all_people.items(), start=1):
        if i % 10000 == 0:
            curr_time = datetime.now().strftime('%H:%M')
            print(f"[{curr_time}] {i:,} / {total_people:,}, {i * 100 / total_people:.2f}% complete")
        row = k.split(key_separator) + [1 if org in v else 0 for org in valid_orgs] + [len(v)]
        try:
            df.loc[len(df)] = row
        except Exception as e:
            print(row)
            raise

    df.to_csv(all_people_csv, index=False)


def list_org_columns():
    """List orgs that don't have at least 'First Name' and 'Last Name' columns"""
    orgs = open(org_names_file).read().split('\n')
    min_cols = {'First Name', 'Last Name'}
    for org in orgs:
        df = pd.read_csv(f'{input_dir}/output/{org}.csv')
        cols = set(list(df.columns))
        if cols.issuperset(min_cols):
            continue
        print(org, ':', list(df.columns))
        print('-' * 10)


def find_suspected_duplicates():
    all_people = [p.split(key_separator) for p in json.load(open(all_people_json)).keys()]

    # Process fields to remove leading/trailing spaces and convert to lowercase
    all_people = [[field.strip().lower() for field in person] for person in all_people]

    # Create 3 dictionaries where the keys are first name + last name, email address, phone number
    all_by_name = defaultdict(list)
    all_by_email = defaultdict(list)
    all_by_phone = defaultdict(list)

    for p in all_people:
        all_by_name[f'{p[0]} {p[1]}'].append(p)
        all_by_email[p[3]].append(p)
        all_by_phone[p[4]].append(p)

    invalid_phone_values = ['', 'none', 'y', 'no call', 'null, null', 'x', 'nocall']
    invalid_email_values = ['', 'none', 'nan', 'n/a']

    all_by_name = {k: v for k, v in all_by_name.items() if len(v) > 1}
    all_by_email = {k: v for k, v in all_by_email.items() if
                    k not in invalid_email_values and len(v) > 1}
    all_by_phone = {k: v for k, v in all_by_phone.items() if
                    k not in invalid_phone_values and len(v) > 1}

    all_duplicates = dict(by_name=all_by_name, by_email=all_by_email, by_phone=all_by_phone)

    print('Duplicates by name:', f'{len(all_by_name):,}')
    print('Duplicates by email:', f'{len(all_by_email):,}')
    print('Duplicates by phone:', f'{len(all_by_phone):,}')

    # Save the duplicates to a JSON file
    json.dump(all_duplicates, open(duplicates_json, 'w'), indent=2)


def update_org_count_per_person():
    all_people = pd.read_csv(all_people_csv)
    all_people['Total Orgs'] = all_people[all_people.columns[5:]].sum(axis=1)
    all_people.to_csv(all_people_csv, index=False)


def update_zip_code():
    def extract_zip_code(address):
        try:
            parsed_address = usaddress.tag(address)
            components = parsed_address[0]
            return components.get('ZipCode', '')  # Return ZIP code if found
        except usaddress.RepeatedLabelError:
            return ''

    all_people = pd.read_csv(all_people_csv, nrows=5).astype(str)
    all_people['Zip Code'] = all_people['Physical Address'].apply(extract_zip_code)

    cols = list(all_people.columns)
    physical_address_index = cols.index('Physical Address')

    cols = cols[:physical_address_index + 1] + ['Zip Code'] + cols[physical_address_index + 2:-1]
    all_people = all_people[cols]

    all_people.to_csv(all_people_csv, index=False)


def main():
    """ """
    # convert_files()
    # generate_org_list()
    # list_org_columns()
    # merge_files()
    # generate_output_file()
    # find_suspected_duplicates()
    update_org_count_per_person()
    # update_zip_code()


if __name__ == "__main__":
    main()
