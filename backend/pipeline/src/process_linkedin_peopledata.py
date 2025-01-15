#!/usr/bin/env python3
import csv
import json
from pathlib import Path


def extract_data_from_json(json_str):
    """Extract raw companies and schools arrays from LinkedIn JSON data."""
    try:
        # Handle both string and dict input
        if isinstance(json_str, str):
            data = json.loads(json_str)
        elif isinstance(json_str, dict):
            data = json_str
        else:
            print(f"Invalid JSON data type: {type(json_str)}")
            return None, None

        # Extract raw companies array
        companies = None
        if isinstance(data, dict) and "positions" in data:
            positions = data.get("positions", {})
            if isinstance(positions, dict) and "positionHistory" in positions:
                companies = positions["positionHistory"]

        # Extract raw schools array
        schools = None
        if isinstance(data, dict) and "schools" in data:
            schools_data = data.get("schools", {})
            if isinstance(schools_data, dict) and "educationHistory" in schools_data:
                schools = schools_data["educationHistory"]

        return companies, schools
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        print(f"Error processing JSON: {e}")
        return None, None


def extract_names_from_json(json_str):
    """Extract company and education names from LinkedIn JSON data."""
    try:
        # Handle both string and dict input
        if isinstance(json_str, str):
            data = json.loads(json_str)
        elif isinstance(json_str, dict):
            data = json_str
        else:
            print(f"Invalid JSON data type: {type(json_str)}")
            return [], []

        # Extract company names from positions
        companies = set()
        if isinstance(data, dict) and "positions" in data:
            positions = data.get("positions", {})
            if isinstance(positions, dict) and "positionHistory" in positions:
                position_history = positions["positionHistory"]
                if isinstance(position_history, list):
                    for position in position_history:
                        if isinstance(position, dict):
                            company_name = position.get("companyName")
                            if company_name:
                                companies.add(company_name)

        # Extract education institutions from schools
        schools = set()
        if isinstance(data, dict) and "schools" in data:
            schools_data = data.get("schools", {})
            if isinstance(schools_data, dict) and "educationHistory" in schools_data:
                education_history = schools_data["educationHistory"]
                if isinstance(education_history, list):
                    for school in education_history:
                        if isinstance(school, dict):
                            school_name = school.get("schoolName")
                            if school_name:
                                schools.add(school_name)

        return list(companies), list(schools)
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        print(f"Error processing JSON: {e}")
        return [], []


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
            print(f"\nReading processed file: {processed_file}")
            with open(processed_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not reader:
                    print("Warning: Failed to create DictReader")
                    return {}, None, []
                fieldnames = reader.fieldnames
                if not fieldnames:
                    print("Warning: No fieldnames found in reader")
                    return {}, None, []
                for row in reader:
                    existing_rows.append(row)
                    if not row:
                        continue
                    # Handle BOM in column name (case-insensitive match at end only)
                    linkedin_url_key = next(
                        (k for k in row.keys() if k and k.lower().endswith('linkedinurl')), '')
                    if not linkedin_url_key:
                        continue
                    linkedin_url = row.get(linkedin_url_key, '').strip()
                    if linkedin_url:
                        processed_data[linkedin_url] = row
                     #   print(f"Added processed data for: {linkedin_url}")
            print(f"Loaded {len(processed_data)} existing processed records")
        return processed_data, fieldnames, existing_rows
    except Exception as e:
        print(f"Error loading processed data: {e}")
        return {}, None, []


def process_csv(input_file, output_file, processed_file=None):
    """
    Process the CSV file and add company and education columns.
    Preserves existing data in the output file and only adds new records.

    Args:
        input_file: Path to input CSV file (string or Path)
        output_file: Path to output CSV file (string or Path)
        processed_file: Path to existing processed file (string or Path)

    Returns:
        Path object of the output file
    """
    # Convert paths to Path objects
    input_file = Path(input_file)
    output_file = Path(output_file)

    # Load existing processed data from processed_file if provided, otherwise from output_file
    processed_file = processed_file if processed_file else output_file
    print(f"\nLoading processed data from: {processed_file}")
    processed_data, existing_fieldnames, existing_rows = load_processed_data(
        processed_file)
    print(f"Loaded {len(existing_rows)} existing rows")

    # Read and process new data
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        input_fieldnames = list(reader.fieldnames)  # Convert to list to modify

        # Define base fields (original fields without linkedin_json)
        base_fields = [f for f in input_fieldnames if f != 'linkedin_json']
        # Define new fields to add before linkedin_json
        new_fields = [
            'Education Institutions',
            'Companies'
        ]
        # Construct final fieldnames list
        fieldnames = base_fields + new_fields
        if 'linkedin_json' in input_fieldnames:
            fieldnames.append('linkedin_json')

        # Clean and validate existing rows
        cleaned_rows = []
        for row in existing_rows:
            # Create a new row with all fields initialized to empty string
            cleaned_row = {field: '' for field in fieldnames}
            # Copy over any existing values
            for field in row.keys():
                if field in fieldnames:  # Only copy fields that are in our schema
                    cleaned_row[field] = row[field]
            cleaned_rows.append(cleaned_row)

        new_records = 0
        all_rows = cleaned_rows  # Use cleaned existing rows

        print(f"\nProcessing input file: {input_file}")

        # Process each row
        row_count = 0
        for row in reader:
            if not row:
                continue
            # Handle BOM in column name (case-insensitive match at end only)
            linkedin_url_key = next(
                (k for k in row.keys() if k and k.lower().endswith('linkedinurl')), '')
            if not linkedin_url_key:
                continue
            linkedin_url = row.get(linkedin_url_key, '').strip()

            # Skip if already processed
            if linkedin_url in processed_data:
                continue

            processed_row = row.copy()
            try:
                # Get the JSON data
                json_str = row.get('linkedin_json', '')
                if json_str and json_str.strip() and json_str.strip() != 'nan':
                    # Extract names for columns
                    companies, schools = extract_names_from_json(json_str)
                    processed_row['Education Institutions'] = json.dumps(
                        sorted(schools), ensure_ascii=False) if schools else '[]'
                    processed_row['Companies'] = json.dumps(
                        sorted(companies), ensure_ascii=False) if companies else '[]'
                else:
                    processed_row['Education Institutions'] = '[]'
                    processed_row['Companies'] = '[]'

                # Ensure all fields exist
                for field in fieldnames:
                    if field not in processed_row:
                        processed_row[field] = ''

                # Add the new record to our collection
                all_rows.append(processed_row)
                new_records += 1
                processed_data[linkedin_url] = processed_row

            except Exception as e:
                print(f"Error processing row: {e}")
                continue

        # Write all rows to the output file
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rows)
        except Exception as e:
            print(f"Error writing to output file: {e}")
            return None

    print(f"Added {new_records} new records to {
          len(processed_data) - new_records} existing records")
    return output_file


def main():
    import sys
    if len(sys.argv) != 3:
        print("Usage: python process_linkedin_peopledata.py <input_file> <output_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    process_csv(input_file, output_file)


if __name__ == "__main__":
    main()
