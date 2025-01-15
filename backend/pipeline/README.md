# Warm Intro Pipeline

A data processing pipeline for analyzing LinkedIn connections and company data to facilitate warm introductions. The pipeline takes a LinkedIn connections.csv file as input, using the ScrapIn API to add profile information for each connection. For all companies in the connection's work and education history, detailed information on each company is also added from the ScrapIn API. The pipeline can be run for as many connections.csv files as desired for colleagues at one company, creating a combined set of people and companies that are available for introductions within the set of colleagues.

## Overview

This pipeline processes LinkedIn connection data to:
1. Extract and enrich LinkedIn profile information
2. Process and standardize profile data
3. Generate company lists from profiles
4. Fetch and enrich company information

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Directory Structure

The pipeline expects and creates the following directory structure:

```
your-company-name/                 # Current directory when running scripts
├── user1-connections.csv          # Input LinkedIn connections file for user1
├── user2-connections.csv          # Input LinkedIn connections file for user2
├── user...n-connections.csv       # Input LinkedIn connections file for user...n
├── interim/                       # Created automatically for intermediate files
│   ├── user1-connections_withLinkedInData.csv
│   ├── user1-connections_company-list.csv
│   ├── user1-connections_company-list_withLinkedInData.csv
│   ├── user2-connections_withLinkedInData.csv
│   ├── user2-connections_company-list.csv
│   └── user2-connections_company-list_withLinkedInData.csv
└── processed/                     # Created automatically for final output
    ├── your-company-name_people_processed.csv      # Uses current directory name
    ├── your-company-name_people_processed_withContacts.csv  # Optional enriched file
    └── your-company-name_companies_processed.csv   # Uses current directory name
```

## Pipeline Usage

**Important**: All scripts must be run from within your company directory. The scripts use the current directory name as the company name for processed files. For example:

```bash
cd Your Company Name
python run_pipeline.py user1-connections.csv
```

This ensures that:
1. Input files are found correctly
2. Output files are created in the right directories
3. Company name is extracted correctly from the current directory
4. Processed files are named correctly with your company name

The input CSV file must contain a 'LinkedinURL' column with profile URLs.

### Pipeline Steps

1. **Profile Data Fetching**: Retrieves detailed LinkedIn profile information using get_people.py
2. **People Data Processing**: Standardizes and enriches profile information using process_linkedin_peopledata.py
3. **Company Extraction**: Creates a unique list of companies from profiles using extract_company_list.py
4. **Company Data Fetching**: Fetches detailed company information using get_companies.py
5. **Company Data Processing**: Processes and standardizes company information using process_linkedin_companydata.py

## Individual Scripts

All scripts must be run from within your company directory:

### get_people.py
Fetches LinkedIn profile data for each person in the input CSV.
```bash
cd Your Company Name
python get_people.py user1-connections.csv
```

### process_linkedin_peopledata.py
Processes raw LinkedIn profile data to extract and standardize information.
```bash
cd Your Company Name
python process_linkedin_peopledata.py interim/user1-connections_withLinkedInData.csv processed/your-company-name_people_processed.csv
```

### extract_company_list.py
Extracts a unique list of companies from processed profile data.
```bash
cd Your Company Name
python extract_company_list.py processed/your-company-name_people_processed.csv interim/user1-connections_company-list.csv
```

### get_companies.py
Fetches detailed company information for the extracted company list.
```bash
cd Your Company Name
python get_companies.py interim/user1-connections_company-list.csv
```

### process_linkedin_companydata.py
Processes raw company data to standardize and structure company information.
```bash
cd Your Company Name
python process_linkedin_companydata.py interim/user1-connections_company-list_withLinkedInData.csv processed/your-company-name_companies_processed.csv
```

### enrich_contacts.py (Post-Processing)
Enriches the processed people file with contact information (email, phone) from a contacts CSV file. This script can be run after the main pipeline as an optional post-processing step.

```bash
cd Your Company Name
python enrich_contacts.py processed/your-company-name_people_processed.csv path/to/contacts.csv [--debug]
```

The contacts CSV file should contain the following columns:
- FirstName: First name of the contact
- LastName: Last name of the contact
- Emails: Email addresses (comma-separated)
- PhoneNumbers: Phone numbers (comma-separated)

The script uses fuzzy name matching with a 95% threshold to ensure high-quality matches. It creates a new file with "_withContacts" suffix containing the original data plus:
- Email_enriched: Matched email addresses
- PhoneNumbers_enriched: Matched phone numbers

Use the --debug flag for detailed logging of the matching process.

## File Formats

### Input Files

#### connections.csv
Required columns:
- LinkedinURL: URL of the LinkedIn profile

### Output Files

#### people_processed.csv
Contains processed profile information including:
- Name
- Current role
- Company
- Location
- Industry
- Education
- Skills

#### people_processed_withContacts.csv (Optional)
Contains all columns from people_processed.csv plus:
- Email_enriched: Email addresses from matched contacts
- PhoneNumbers_enriched: Phone numbers from matched contacts

#### companies_processed.csv
Contains processed company information including:
- Company name
- Industry
- Size
- Location
- Description
- Website

## Dependencies

Key dependencies include:
- pandas: Data processing and manipulation
- aiohttp: Asynchronous HTTP requests
- unidecode: Text normalization
- thefuzz: String matching and comparison

See `requirements.txt` for complete list of dependencies.
