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
    key_separator,
    merge_candidates_json, dtype_dict
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

    # Clean up the phone numbers and emails
    phones = df['Cell Phone Number'].str.replace(r'[-() ]', '', regex=True).str.replace('nan', '')
    emails = df['Email Address'].str.replace('nan', '')
    df['Cell Phone Number'] = phones
    df['Email Address'] = emails

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
            parsed_address = usaddress.tag(str(address))
            components = parsed_address[0]
            zip_code = components.get('ZipCode', '').split('-')[0].strip()
            return zip_code.zfill(5) if zip_code else ''
        except usaddress.RepeatedLabelError:
            return ''

    all_people = read_all_people_file()
    zip_code = all_people['Physical Address'].apply(extract_zip_code).astype(str)
    all_people['Zip Code'] = zip_code

    cols = list(all_people.columns)
    physical_address_index = cols.index('Physical Address')

    cols = cols[:physical_address_index + 1] + ['Zip Code'] + cols[physical_address_index + 1:-1]
    all_people = all_people[cols]

    all_people.to_csv(all_people_csv, index=False)


def clean_phone_numbers():
    all_people = read_all_people_file()
    phone_numbers = (all_people['Cell Phone Number']
                     .astype(str)
                     .str.replace(r'[-() ]', '', regex=True)
                     .str.replace('nan', ''))
    all_people['Cell Phone Number'] = phone_numbers
    all_people.to_csv(all_people_csv, index=False)


def clean_nans(cols):
    all_people = read_all_people_file()
    for col in cols:
        values = all_people[col].astype(str).str.replace('nan', '')
        all_people[col] = values
    all_people.to_csv(all_people_csv, index=False)


def read_all_people_file():
    df = pd.read_csv(all_people_csv, dtype=dtype_dict, low_memory=False).astype(str)
    return df


def merge_candidates():
    def add_person_to_unique_people(person):
        """"""
        # unique_people.loc[len(unique_people)] = person

    def read_field(name):
        return row[name].strip().lower().replace('nan', '')

    d = dict(people_without_full_name_and_email=defaultdict(list),
             people_with_full_name_and_address=defaultdict(list),
             people_with_full_name_and_cell_phone=defaultdict(list),
             people_with_full_name_only=defaultdict(list))

    all_people = read_all_people_file()
    unique_people = pd.DataFrame(columns=all_people.columns)

    total_people = len(all_people)
    for i, row in all_people.iterrows():
        if i % 10000 == 0:
            curr_time = datetime.now().strftime('%H:%M')
            print(f"[{curr_time}] {i:,} / {total_people:,}, {i * 100 / total_people:.2f}% complete")

        first_name = read_field('First Name')
        last_name = read_field('Last Name')
        email = read_field('Email Address')
        address = read_field('Physical Address')
        cell_phone = read_field('Cell Phone Number')

        has_full_name = first_name and last_name

        # If a person has a full name and email just add them to the output
        if has_full_name and email:
            add_person_to_unique_people(row)
            continue
        # If the email are not empty, add the person to the dictionary

        if email:
            d['people_without_full_name_and_email'][
                f'{first_name}, {last_name},{email}'].append(list(row))
        if not has_full_name:
            continue

        # If the full name and address are not empty, add the person to the dictionary
        elif first_name and last_name and address:
            d['people_with_full_name_and_address'][
                f'{first_name}, {last_name}, {address}'].append(list(row))
        # If the full name and cell phone are not empty, add the person to the dictionary
        elif first_name and last_name and cell_phone:
            d['people_with_full_name_and_cell_phone'][
                f'{first_name}, {last_name}, {cell_phone}'].append(list(row))
        elif:
            d['people_with_full_name_only'][
                f'{first_name}, {last_name}'].append(list(row))

    # Remove people that appear only once in any dictionary
    for k, v in d.items():
        people = [vv[0] for vv in v.values() if len(vv) ==1]
        for person in people:
            add_person_to_unique_people(person)
        d[k] = {kk: vv for kk, vv in v.items() if len(vv) > 1}


    # Print stats
    # print('People with duplicates (already in output df:', len(output))
    print('People without full name and email:',
          len(d['people_without_full_name_and_email']))
    print('People with full name and address:', len(d['people_with_full_name_and_address']))
    print('People with full name and cell phone:',
          len(d['people_with_full_name_and_cell_phone']))

    # Save the dictionaries to a JSON file
    json.dump(d, open(merge_candidates_json, 'w'), indent=2)



def main():
    """ """
    # convert_files()
    # generate_org_list()
    # list_org_columns()
    # merge_files()
    # generate_output_file()
    # find_suspected_duplicates()
    # update_org_count_per_person()
    # update_zip_code()
    # clean_phone_numbers()
    # clean_nans([
    #   'First Name', 'Last Name', 'Physical Address', 'Email Address'])
    merge_candidates()


if __name__ == "__main__":
    main()
