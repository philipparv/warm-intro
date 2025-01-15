import pandas as pd
import json
import os


def get_company_info_from_position(position):
    """Extract company URL and name from a single position"""
    if not isinstance(position, dict):
        return None

    linkedin_url = position.get('linkedInUrl', '')
    company_name = position.get('companyName', '')

    # Only include companies with valid LinkedIn URLs
    if not linkedin_url or 'linkedin.com/search/' in linkedin_url or 'keywords=' in linkedin_url:
        return None

    # Only include companies with actual company pages
    if 'linkedin.com/company/' not in linkedin_url:
        return None

    company_info = {
        'company_linkedin_url': linkedin_url,
        'company_name': company_name
    }

    return company_info


def get_company_info(positions):
    """Extract company URLs and names from all positions"""
    if not isinstance(positions, dict) or 'positionHistory' not in positions:
        return []

    position_history = positions['positionHistory']
    if not isinstance(position_history, list):
        return []

    # Process all positions
    companies = []
    for position in position_history:
        company_info = get_company_info_from_position(position)
        if company_info:
            companies.append(company_info)

    return companies


def process_linkedin_data(input_file, output_file=None):
    """
    Process LinkedIn data from input CSV and create new CSV with company information.

    Args:
        input_file: Path to input CSV file
        output_file: Optional path to output CSV file. If not provided, will be generated from input file name.
    """
    # If output_file not provided, generate from input file
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        base_name = base_name.replace(
            '_withLinkedInData_processed', '')  # Remove existing suffixes
        output_file = os.path.join(os.path.dirname(input_file), f"{
                                   base_name}_company-list.csv")

    # Read input CSV with explicit UTF-8 encoding
    df = pd.read_csv(input_file, encoding='utf-8')

    # Initialize lists to store extracted data
    company_data = []

    # Process each row
    for _, row in df.iterrows():
        try:
            # Get the JSON string
            json_str = row.get('linkedin_json', '')
            if not json_str or not isinstance(json_str, str) or json_str.strip() == 'nan':
                continue

            # Parse JSON data with proper Unicode handling
            linkedin_data = json.loads(json_str)
            if not isinstance(linkedin_data, dict):
                print(f"Invalid JSON data type: {type(linkedin_data)}")
                continue

            # Get positions data
            positions = linkedin_data.get('positions')
            if not isinstance(positions, dict):
                continue

            # Get company information from positions
            companies = get_company_info(positions)
            company_data.extend(companies)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error processing row: {e}")
            continue

    # Create new DataFrame with extracted data and remove duplicates
    # Use both URL and name for deduplication to ensure truly unique companies
    output_df = pd.DataFrame(company_data).drop_duplicates(
        subset=['company_linkedin_url', 'company_name'])

    # Sort by company name
    output_df = output_df.sort_values('company_name')

    # Write to CSV with explicit UTF-8 encoding
    output_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Processed data written to {output_file}")
    print(f"Extracted {len(output_df)
                       } unique companies with valid LinkedIn URLs")

    return output_file


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(
            "Usage: python extract_company_list.py <input_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    process_linkedin_data(input_file, output_file)
