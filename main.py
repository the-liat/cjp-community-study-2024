import csv
from datetime import datetime
import json
import os
import time
from collections import defaultdict, OrderedDict
from glob import glob
from pprint import pprint as pp
import numpy as np
import pandas as pd
import usaddress
from pyxdameraulevenshtein import damerau_levenshtein_distance
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
    merge_candidates_json, dtype_dict, final_merged_people_csv
)


def convert_files():
    os.makedirs(target_dir, exist_ok=True)
    # Read file list from target directory (*.xlsx)
    files = glob(f'{input_dir}/*.xlsx')
    for f in files:
        base_name = os.path.basename(f)
        csv_file = f'{input_dir}/output/{base_name.replace(".xlsx", ".csv")}'
        if os.path.isfile(csv_file):
            continue
        sheets = pd.read_excel(f, sheet_name=None)  # Returns a dictionary of DataFrames
        df = list(sheets.values())[0]  # Save each sheet as a CSV
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


# def standardize_names(rows):
#     """find people with similar names and rename to first person's name
#     """
#     print('standardize_names() - start')
#     for i, person in enumerate(rows):
#         if i % 100 == 0:
#             print(f'[{datetime.now().strftime("%H:%M")} {i * 100} / {len(rows)} % complete')
#         name = person[0] + ' ' + person[1]
#         for j, p in enumerate(rows[i+1:]):
#             name2 = p[0] + ' ' + p[1]
#             if name == name2:
#                 continue
#             if damerau_levenshtein_distance(name, name2) < 3:
#                 p[0] = person[0]
#                 p[1] = person[1]


def generate_output_file():
    """ Create a DataFrame from the dictionary where the columns the details of a person + all org
        names and the values are 0 or 1 depending on whether the person is on that org list
    """
    all_people = json.load(open(all_people_json))
    valid_orgs = open(org_names_file).read().split('\n')
    cols = col_list + valid_orgs + ['Total Orgs']

    # Accumulate rows in a list to avoid repeated appending
    rows = []
    total_people = len(all_people)

    for i, (k, v) in enumerate(all_people.items(), start=1):
        if i % 10000 == 0:
            curr_time = datetime.now().strftime('%H:%M')
            print(f"[{curr_time}] {i:,} / {total_people:,}, {i * 100 / total_people:.2f}% complete")

        row = k.split(key_separator) + [1 if org in v else 0 for org in valid_orgs] + [len(v)]
        rows.append(row)

    #rows2 = standardize_names(rows)
    # Convert the accumulated rows to a DataFrame at once
    df = pd.DataFrame(rows, columns=cols)

    # Clean up the phone numbers and emails
    phones = df['Cell Phone Number'].str.replace(r'[-() ]+', '', regex=True).str.replace('nan', '')
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

def find_matching_name(all_names, name):
    for n in all_names:
        if damerau_levenshtein_distance(n, name) < 3:
            return n
    return name

def find_suspected_duplicates():
    all_people = [p.split(key_separator) for p in json.load(open(all_people_json)).keys()]

    # Process fields to remove leading/trailing spaces and convert to lowercase
    all_people = [[field.strip().lower() for field in person] for person in all_people]

    # Create 3 dictionaries where the keys are first name + last name, email address, phone number
    all_by_name = defaultdict(list)
    all_by_email = defaultdict(list)
    all_by_phone = defaultdict(list)

    for p in all_people:
        name = f'{p[0]} {p[1]}'
        name = find_matching_name(all_by_name.keys(), name)
        all_by_name[name].append(p)
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


def clean_addresses():
    def clean_address(address):
        def abbrev_state(state_name):
            d = {
                'Alabama': 'AL',
                'Alaska': 'AK',
                'Arizona': 'AZ',
                'Arkansas': 'AR',
                'California': 'CA',
                'Colorado': 'CO',
                'Connecticut': 'CT',
                'Delaware': 'DE',
                'District of Columbia': 'DC',
                'Florida': 'FL',
                'Georgia': 'GA',
                'Hawaii': 'HI',
                'Idaho': 'ID',
                'Illinois': 'IL',
                'Indiana': 'IN',
                'Iowa': 'IA',
                'Kansas': 'KS',
                'Kentucky': 'KY',
                'Louisiana': 'LA',
                'Maine': 'ME',
                'Maryland': 'MD',
                'Massachusetts': 'MA',
                'Michigan': 'MI',
                'Minnesota': 'MN',
                'Mississippi': 'MS',
                'Missouri': 'MO',
                'Montana': 'MT',
                'Nebraska': 'NE',
                'Nevada': 'NV',
                'New Hampshire': 'NH',
                'New Jersey': 'NJ',
                'New Mexico': 'NM',
                'New York': 'NY',
                'North Carolina': 'NC',
                'North Dakota': 'ND',
                'Ohio': 'OH',
                'Oklahoma': 'OK',
                'Oregon': 'OR',
                'Pennsylvania': 'PA',
                'Rhode Island': 'RI',
                'South Carolina': 'SC',
                'South Dakota': 'SD',
                'Tennessee': 'TN',
                'Texas': 'TX',
                'Utah': 'UT',
                'Vermont': 'VT',
                'Virginia': 'VA',
                'Washington': 'WA',
                'West Virginia': 'WV',
                'Wisconsin': 'WI',
                'Wyoming': 'WY'
            }

            return d.get(state_name.title(), 'MA')

        try:
            parsed_address = usaddress.tag(str(address))
            c = parsed_address[0]
            address = ' '.join((c.get('AddressNumber', ''), c.get('StreetName', ''),
            c.get('StreetNamePostType'),
                               c.get('PlaceName', ''), abbrev_state(c.get('StateName')))).lower()
        except Exception:
            return address.lower()

    all_people = read_all_people_file()
    all_people['Physical Address'].apply(clean_address).astype(str)

    all_people.to_csv(all_people_csv, index=False)


def clean_phone_numbers():
    all_people = read_all_people_file()
    phone_numbers = (all_people['Cell Phone Number']
                     .astype(str)
                     .str.replace(r'[-() ]', '', regex=True)
                     .str.replace('nan', '')
                     .str.replace('+', ''))
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
    def merge_people_with_same_name_and_email(d: dict, col_names):
        people1 = []
        for candidates in d.values():
            p = OrderedDict()
            first = candidates[0]
            # find all valid values if exist per field of each candidate
            addresses = [c[2] for c in candidates if c[2]]
            zipcodes = [c[3] for c in candidates if c[3]]
            phones = [c[5] for c in candidates if c[5]]
            address1 = addresses[0] if addresses else ''
            # Populate the person's details
            p['First Name'] = first[0]
            p['Last Name'] = first[1]
            p['Physical Address'] = f'''"{address1}"'''
            p['Zip Code'] = zipcodes[0] if zipcodes else ''
            p['Email Address'] = first[4]
            p['Cell Phone Number'] = phones[0] if phones else ''
            # Populate orgs
            total = 0
            for i in range(6, len(first) - 1):
                member = max([int(c[i]) for c in candidates])
                total += member
                p[col_names[i]] = member

            p['Total Orgs'] = total
            people1.append(list(p.values()))
        return people1

    def merge_people_with_same_email_and_no_name(d: dict, col_names):
        people2 = []
        for candidates in d.values():
            p = OrderedDict()
            first = candidates[0]
            # find all valid values if exist per field of each candidate
            addresses = [c[2] for c in candidates if c[2]]
            zipcodes = [c[3] for c in candidates if c[3]]
            phones = [c[5] for c in candidates if c[5]]
            address2 = addresses[0] if addresses else ''
            # Populate the person's details
            p['First Name'] = first[0]
            p['Last Name'] = first[1]
            p['Physical Address'] = f'''"{address2}"'''
            p['Zip Code'] = zipcodes[0] if zipcodes else ''
            p['Email Address'] = first[4]
            p['Cell Phone Number'] = phones[0] if phones else ''
            # Populate orgs
            total = 0
            for i in range(6, len(first) - 1):
                member = max([int(c[i]) for c in candidates])
                total += member
                p[col_names[i]] = member

            p['Total Orgs'] = total
            people2.append(list(p.values()))
        return people2

    def merge_people_with_same_name_and_address(d: dict, col_names):
        people3 = []
        for candidates in d.values():
            p = OrderedDict()
            first = candidates[0]
            # find all valid values if exist per field of each candidate
            zipcodes = [c[3] for c in candidates if c[3]]
            phones = [c[5] for c in candidates if c[5]]
            emails = [c[4] for c in candidates if c[4]]
            # Populate the person's details
            p['First Name'] = first[0]
            p['Last Name'] = first[1]
            p['Physical Address'] = f'"{first[2]}"'
            p['Zip Code'] = zipcodes[0] if zipcodes else ''
            p['Email Address'] = emails[0] if emails else ''
            p['Cell Phone Number'] = phones[0] if phones else ''
            # Populate orgs
            total = 0
            for i in range(6, len(first) - 1):
                member = max([int(c[i]) for c in candidates])
                total += member
                p[col_names[i]] = member

            p['Total Orgs'] = total
            people3.append(list(p.values()))
        return people3

    def merge_people_with_same_name_and_cell_phone(d: dict, col_names):
        people4 = []
        for candidates in d.values():
            p = OrderedDict()
            first = candidates[0]
            # find all valid values if exist per field of each candidate
            addresses = [c[2] for c in candidates if c[2]]
            zipcodes = [c[3] for c in candidates if c[3]]
            emails = [c[4] for c in candidates if c[4]]
            address4 = addresses[0] if addresses else ''
            # Populate the person's details
            p['First Name'] = first[0]
            p['Last Name'] = first[1]
            p['Physical Address'] = f'''"{address4}"'''
            p['Zip Code'] = zipcodes[0] if zipcodes else ''
            p['Email Address'] = emails[0] if emails else ''
            p['Cell Phone Number'] = first[5]
            # Populate orgs
            total = 0
            for i in range(6, len(first) - 1):
                member = max([int(c[i]) for c in candidates])
                total += member
                p[col_names[i]] = member

            p['Total Orgs'] = total
            people4.append(list(p.values()))
        return people4

    def merge_people_with_same_name_only(d: dict, col_names):
        people5 = []
        for candidates in d.values():
            p = OrderedDict()
            first = candidates[0]
            # find all valid values if exist per field of each candidate
            addresses = [c[2] for c in candidates if c[2]]
            zipcodes = [c[3] for c in candidates if c[3]]
            phones = [c[5] for c in candidates if c[5]]
            emails = [c[4] for c in candidates if c[4]]
            address5 = addresses[0] if addresses else ''
            # Populate the person's details
            p['First Name'] = first[0]
            p['Last Name'] = first[1]
            p['Physical Address'] = f'"{address5}"'
            p['Zip Code'] = zipcodes[0] if zipcodes else ''
            p['Email Address'] = emails[0] if emails else ''
            p['Cell Phone Number'] = phones[0] if phones else ''
            # Populate orgs
            total = 0
            for i in range(6, len(first) - 1):
                member = max([int(c[i]) for c in candidates])
                total += member
                p[col_names[i]] = member

            p['Total Orgs'] = total
            people5.append(list(p.values()))
        return people5

    def read_field(name):
        return row[name].strip().lower().replace('nan', '')

    d = dict(people_without_full_name_and_email=defaultdict(list),
             people_with_full_name_and_email=defaultdict(list),
             people_with_full_name_and_address=defaultdict(list),
             people_with_full_name_and_cell_phone=defaultdict(list),
             people_with_full_name_only=defaultdict(list))

    others = []  # people that don't fit any other category (can't be merged)

    all_people = read_all_people_file()
    col_names = list(all_people.columns)

    total_people = len(all_people)
    for i, row in all_people.iterrows():
        if i % 10000 == 0:
            curr_time = datetime.now().strftime('%H:%M')
            print(f"[{curr_time}] {i:,} / {total_people:,}, {i * 100 / total_people:.2f}% complete")

        first_name = read_field('First Name')
        last_name = read_field('Last Name')
        email = read_field('Email Address')
        address = f'''"{read_field('Physical Address')}"'''
        cell_phone = read_field('Cell Phone Number')

        has_full_name = first_name and last_name
        if has_full_name and email:
            d['people_with_full_name_and_email'][
                f'{first_name}, {last_name}, {email}'].append(list(row))
        elif email:
            d['people_without_full_name_and_email'][
                f'{first_name}, {last_name}, {email}'].append(list(row))
        elif has_full_name and address:
            d['people_with_full_name_and_address'][
                f'{first_name}, {last_name}, {address}'].append(list(row))
        elif has_full_name and cell_phone:
            d['people_with_full_name_and_cell_phone'][
                f'{first_name}, {last_name}, {cell_phone}'].append(list(row))
        elif not (address or cell_phone):
            d['people_with_full_name_only'][
                f'{first_name}, {last_name}'].append(list(row))
        else:
            others.append(list(row))

    # Print stats
    print('People with full name and email:', len(d['people_with_full_name_and_email']))
    print('People with email, but without full name:', len(d['people_without_full_name_and_email']))
    print('People with full name and address:', len(d['people_with_full_name_and_address']))
    print('People with full name and cell phone:', len(d['people_with_full_name_and_cell_phone']))
    print('People with full name only:', len(d['people_with_full_name_only']))

    people = others
    people += merge_people_with_same_name_and_email(d['people_with_full_name_and_email'], col_names)
    people += merge_people_with_same_email_and_no_name(d['people_without_full_name_and_email'],
                                                       col_names)
    people += merge_people_with_same_name_and_address(d['people_with_full_name_and_address'],
                                                      col_names)
    people += merge_people_with_same_name_and_cell_phone(d['people_with_full_name_and_cell_phone'],
                                                         col_names)
    people += merge_people_with_same_name_only(d['people_with_full_name_only'], col_names)
    people = [[x if x != 'nan' else '' for x in p] for p in people]

    # Creating the CSV file
    with open(final_merged_people_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the column names
        writer.writerow(col_names)

        # Write the data rows
        writer.writerows(people)
        print("CSV file created successfully.")


def main():
    """ """
    # convert_files()
    # generate_org_list()
    # list_org_columns()
    # merge_files()
    #generate_output_file()
    # find_suspected_duplicates()
    #update_org_count_per_person()
    #update_zip_code()
    #clean_addresses()
    #clean_phone_numbers()
    #clean_nans([
    #'First Name', 'Last Name', 'Physical Address', 'Email Address'])
    #merge_candidates()


if __name__ == "__main__":
    main()
