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
* [x] set up python virtual environment
* [x] convert xslx files to csv
- [x] generate a list of organization by enumerating all the input file
- [ ] Merge all files where each row contains all the personal details for each person and 
 which organization lists that person appeared on (marked as 0=not on that org list or 1=yes on 
  that org list). 
- [ ] Scan all the files. For each file iterate over all the people and store info in a shared dict 
  where the key is the person's details as a tuple and the value is a list of organizations (the 
  file names the person appears on)  
{(first_name, last_name, address, email, phone): [org1,org2,]}
- [ ] Iterate over the entries of the dictionary. 
  - [ ] Each entry will become single row in the output file. the dictionary key will become the 
    same fields in the row. 
  - [ ] Iterate over the organization in the value and set the corresponding fields to "1" in 
    the row
  - [ ] We need a dict that maps org name to field indices in the output file (generate from the 
    org list)
  - [ ] Add another field that will be the number of orgs (len of the dict value)
- the end result will be a csv file 

## creating virtual environment
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

