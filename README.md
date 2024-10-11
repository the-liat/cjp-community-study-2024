# CJP Contact List Analysis

* Categorize oraganizations into: synagogues, schools, human service agencies, JCCs, youth 
  serving organizations, single group advocacy organizations,cultural organizations.
* For any given organization, several types of analysis are possible, for example:

 • The number of unique individuals/households on their list
 • The proportion of individuals/households on their lists that are only on their lists and the 
 proportion that appear on other lists
 • The distribution of the number of other organizational lists (1, 2, 3, 4, etc.) that their 
 individuals/households also appear on
 • The distribution of types of organizations that their individuals/households also appear on
 • The geographic distribution of individuals/households on their lists (assuming geographic 
 data exist)
 • Averages or medians for all organizations that can be used as benchmarks for comparison (e.g.,
 a given organization could compare the proportion of its lists that is unique to it against the
 median unique proportion across all lists)
 
Several analyses examining the contacts list altogether can also be prepared for CJP, for example:
 • The total number of unique households across all lists
 • The distribution of the number of lists (1, 2, 3, 4, etc.) that individuals/households appear on
 • The distribution of the number of types of organizations (1, 2, 3, 4, etc.) that 
 individuals/households appear on
 • The proportion of all individuals/households that appear on the different types of 
 organizations (e.g., what proportion appear on synagogue lists or social service lists)
 • Among individuals/households that appear on more than one list, substantial clusters of types 
 of organizations they appear on
 • The geographic distribution of individuals/households across all lists combined and within 
 each type of organization (assuming geographic data exist)
## Plan
- [x] set up python virtual environment
- [x] convert xslx files to csv
- [x] generate a list of organization by enumerating all the input file
- [x] Merge all files where each row contains all the personal details for each person and 
 which organization lists that person appeared on (marked as 0=not on that org list or 1=yes on 
  that org list). 
- [x] Scan all the files. For each file iterate over all the people and store info in a shared dict 
  where the key is the person's details as a tuple and the value is a list of organizations (the 
  file names the person appears on) {(first_name, last_name, address, email, phone): [org1,org2,]}
- [x] Iterate over the entries of the dictionary. 
- [x] Each entry will become single row in the output file. the dictionary key will become the 
  same fields in the row. 
- [x] Iterate over the organization in the value and set the corresponding fields to "1" in 
  the row
- [x] Add another field that will be the number of orgs 
- [x]the end result will be a csv file 
- [ ] ***Adjust code to include additional lists***
- [ ] ***Read csv file as data frame and add organization category***

## Creating virtual environment
 ```
 python -m venv venv
 ```
## Activate the virtual environment
```
 .\venv\scripts\activate.ps1
 python
```
## Install dependencies
```
pip install -r requirments.txt
```

## Merge Rules

1. Conflict Resolution: If a person has multiple records with different non-empty values for the 
same field (e.g., two different addresses for the same combination of first name, last name, and email), resolve conflicts by keeping the merging rule and selecting one of the conflicting values randomly for the affected fields.

2. Organization Values: Add organization values (binary values, such as 0s and 1s) across records.

3. Person Identification:

    - A person is uniquely identified if their first name, last name, and at least one additional 
   field (address, phone, or email) match.
    - A person is also identified if their email matches, along with the first name.
4. Field Union: When merging multiple records of the same person where some records are missing 
      values, use the union of all available fields to create a complete merged record.

Note: We recognize that typos or inconsistencies in any field may cause a person to be recognized as multiple individuals across organizations.

## Code Explanation 

1. Imports Libraries: The code begins by importing several Python libraries that are useful for tasks like reading and writing files, manipulating data, and cleaning up text. Examples include csv, pandas (for handling spreadsheets), os (for interacting with the operating system), and others.
2. File Conversion: The convert_files function looks for Excel files (.xlsx) in a specified 
   input directory, reads each file, and converts it to a CSV file format (a text-based spreadsheet).
3. Organization List Generation: The generate_org_list function extracts the organization names 
   from the Excel file names and writes them into a list. This helps keep track of which organizations are being processed.
4. File Merging: The merge_files function reads through all the CSV files, collects personal details (like names and contact information), and notes which organizations each person appears in. It creates a large dictionary of people and their associated organizations.
5. Output Generation: The generate_output_file function creates a large table (DataFrame) where 
   each row contains a person’s details and columns that indicate whether they are associated with specific organizations.
6. Listing Columns: The list_org_columns function checks if the organization files have essential columns like "First Name" and "Last Name." It reports any files that are missing these required columns.
7. Duplicate Detection: The find_suspected_duplicates function identifies people who appear 
   multiple times in different files by checking names, emails, and phone numbers. It saves this duplicate data for further investigation.
8. Additional Data Cleaning: Functions like update_zip_code, clean_phone_numbers, and clean_nans 
   help clean and format the data, such as fixing ZIP codes and removing "nan" (which stands for "Not a Number") values from columns.
9. Merging Candidates: The merge_candidates function tries to merge records of the same person 
   across different organization files, based on details like name, email, and phone number. It combines these duplicate entries into a single entry for each person.
10. Main Function: The main function orchestrates the whole process by calling the appropriate 
    functions to convert, clean, and merge data.
In summary, this code automates the process of combining and cleaning up data from multiple Excel files that contain personal information. It creates a final, cleaned-up CSV file that lists people and the organizations they are associated with, while also identifying duplicates.