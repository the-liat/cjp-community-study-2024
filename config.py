import sys

if sys.platform == 'darwin':
    input_dir = 'contact-lists'
    target_dir = f'{input_dir}/output'
else:
    input_dir = r'C:/Users/Liat Sayfan/Documents/CJP Contact Lists'
    target_dir = input_dir + '/output'


org_names_file = target_dir + '/org_names.txt'
valid_orgs_file = target_dir + '/valid_orgs.txt'
all_people_json = target_dir + '/all_people.json'
all_people_csv = target_dir + '/all_people.csv'
duplicates_json = target_dir + '/duplicates.json'
merge_candidates_json = target_dir + '/merge_candidates.json'
final_merged_people_csv = target_dir + '/final_merged_people.csv'

dtype_dict = {
    'First Name': str,
    'Last Name': str,
    'Physical Address': str,
    'Email Address': str,
    'Cell Phone Number': str,
    'Zip Code': str
}

col_list = [
    'First Name',
    'Last Name',
    'Physical Address',
    'Email Address',
    'Cell Phone Number']

# Using middle dot (alt-shift-9 on Mac, Num Lock on + alt-0183 on Windows - use numeric keypad)
# as a separator
key_separator = '·'
