import sys

if sys.platform == 'darwin':
    input_dir = 'contact-lists'
    target_dir = f'{input_dir}/output'
else:
    input_dir = r'C:/Users/Liat Sayfan/Documents/CJP Contact Lists'
    target_dir = input_dir + '/output'


org_names_file = f'{target_dir}/org_names.txt'
valid_orgs_file = f'{target_dir}/valid_orgs.txt'
all_people_json = f'{target_dir}/all_people.json'
all_people_csv = f'{target_dir}/all_people.csv'
duplicates_json = f'{target_dir}/duplicates.json'

col_list = [
    'First Name',
    'Last Name',
    'Physical Address',
    'Email Address',
    'Cell Phone Number']

# Using middle dot (alt-shift-9 on Mac, Num Lock on + alt-0183 on Windows - use numeric keypad)
# as a separator
key_separator = '·'
