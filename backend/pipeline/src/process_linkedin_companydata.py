#!/usr/bin/env python3
import csv
import json
from pathlib import Path


def has_valid_data(json_str):
    """Check if JSON string or dict contains actual company data."""
    try:
        # Parse JSON if it's a string
        if isinstance(json_str, str):
            if not json_str or json_str.strip() in ['{}', '']:
                print("Empty JSON string")
                return False
            data = json.loads(json_str)
        else:
            data = json_str

        # Debug checks
        if not isinstance(data, dict):
            print("Company data is not a dictionary")
            return False

        return True
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return False
    except AttributeError as e:
        print(f"Attribute error: {e}")
        return False


def extract_company_fields(company_data, row):
    """Extract specific fields from company data and add to row"""
    if not company_data or not isinstance(company_data, dict):
        row.update({
            'website_url': '',
            'industry': '',
            'specialties': '[]',
            'employee_count': '',
            'city': '',
            'geographic_area': '',
            'postal_code': '',
            'founded': '',
            'tagline': '',
            'description': '',
            'logo_url': '',
            'full_json': '{}'
        })
        return row

    # Extract headquarters info
    hq = company_data.get('headquarter', {})

    # Format specialties as JSON array with proper Unicode handling
    specialties = json.dumps(company_data.get(
        'specialities', []), ensure_ascii=False)

    # Extract founded year
    founded = ''
    founded_data = company_data.get('foundedOn', {})
    if isinstance(founded_data, dict):
        founded = str(founded_data.get('year', ''))

    row.update({
        'website_url': company_data.get('websiteUrl', ''),
        'industry': json.dumps(company_data.get('industry', ''))[1:-1] if company_data.get('industry') else '',
        'specialties': specialties,
        'employee_count': str(company_data.get('employeeCount', '')),
        'city': hq.get('city', ''),
        'geographic_area': hq.get('geographicArea', ''),
        'postal_code': hq.get('postalCode', ''),
        'founded': founded,
        'tagline': json.dumps(company_data.get('tagline', ''))[1:-1] if company_data.get('tagline') else '',
        'description': json.dumps(company_data.get('description', ''))[1:-1] if company_data.get('description') else '',
        'logo_url': company_data.get('logo', ''),
        'full_json': json.dumps(company_data, ensure_ascii=False)
    })
    return row


def load_processed_data(processed_file):
    """
    Load existing processed data from the processed file.
    Returns:
    - Dictionary mapping LinkedIn URLs to their data row
    - List of fieldnames from the processed file
    - List of all existing rows
    """
    processed_data = {}
    fieldnames = None
    existing_rows = []

    try:
        if Path(processed_file).exists():
            with open(processed_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    existing_rows.append(row)
                    linkedin_url = row.get('company_linkedin_url', '').strip()
                    if linkedin_url:
                        processed_data[linkedin_url] = row
            print(f"Loaded {len(processed_data)} existing processed records")
        return processed_data, fieldnames, existing_rows
    except Exception as e:
        print(f"Error loading processed data: {e}")
        return {}, None, []


def process_csv(input_file, output_file):
    """
    Process company data from interim CSV file with LinkedIn data into final format.
    Preserves existing data in the output file and only adds new records.

    Args:
        input_file: Path to interim CSV file containing LinkedIn JSON data
        output_file: Path to output processed CSV file
    """
    # Create the output directory if it doesn't exist
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Load existing processed data
    processed_data, existing_fieldnames, existing_rows = load_processed_data(
        output_file)

    # Define fieldnames for processed file
    fieldnames = [
        'company_linkedin_url',
        'company_name',
        'website_url',
        'industry',
        'specialties',
        'employee_count',
        'city',
        'geographic_area',
        'postal_code',
        'founded',
        'tagline',
        'description',
        'logo_url',
        'full_json'
    ]

    success_count = 0
    total_count = 0
    new_records = 0
    all_rows = existing_rows.copy()  # Start with existing rows

    # Read and process the interim file
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            total_count += 1
            print(f"\nProcessing company: {
                  row.get('company_name', 'Unknown')}")
            linkedin_url = row.get('company_linkedin_url', '').strip()

            # Skip if already processed
            if linkedin_url in processed_data:
                continue

            linkedin_json = row.get('linkedin_json', '{}')

            try:
                # Parse JSON string to dict and extract company data
                data = json.loads(linkedin_json) if isinstance(
                    linkedin_json, str) else linkedin_json

                # Extract company data from nested structure if needed
                company_data = data.get('company') if isinstance(
                    data, dict) and 'company' in data else data

                if has_valid_data(company_data):
                    processed_row = {
                        'company_linkedin_url': linkedin_url,
                        'company_name': row['company_name']
                    }
                    processed_row = extract_company_fields(
                        company_data, processed_row)
                    all_rows.append(processed_row)
                    success_count += 1
                    new_records += 1
                    print("Successfully processed company data")
                else:
                    print("Invalid company data")
                    processed_row = {
                        'company_linkedin_url': linkedin_url,
                        'company_name': row['company_name']
                    }
                    processed_row = extract_company_fields(None, processed_row)
                    all_rows.append(processed_row)

            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
                processed_row = {
                    'company_linkedin_url': linkedin_url,
                    'company_name': row['company_name']
                }
                processed_row = extract_company_fields(None, processed_row)
                all_rows.append(processed_row)
            except Exception as e:
                print(f"Unexpected error: {e}")
                processed_row = {
                    'company_linkedin_url': linkedin_url,
                    'company_name': row['company_name']
                }
                processed_row = extract_company_fields(None, processed_row)
                all_rows.append(processed_row)

    # Write all rows to the output file
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nProcessing complete:")
    print(f"Total records processed: {total_count}")
    print(f"New records added: {new_records}")
    print(f"Existing records preserved: {len(existing_rows)}")
    print(f"Successfully processed: {success_count}")
    print(f"Failed to process: {total_count - success_count}")
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python process_linkedin_companydata.py <input_csv> <output_csv>")
        sys.exit(1)

    process_csv(sys.argv[1], sys.argv[2])
