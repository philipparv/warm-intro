#!/usr/bin/env python3
import asyncio
import csv
import json
import sys
import urllib.parse
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from aiolimiter import AsyncLimiter
from pathlib import Path

# Scrapin API configuration
SCRAPIN_API_KEY = "sk_afa1225ba1a380f7efbb1cc98e30479e6201d17d"

# Rate limiter: Max 300 calls per minute
CALLS_PER_MINUTE = 300
limiter = AsyncLimiter(CALLS_PER_MINUTE, time_period=60)


def has_valid_data(json_str):
    """Check if JSON string contains any real data."""
    try:
        if not json_str or json_str.strip() in ['{}', '']:
            return False
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        return bool(isinstance(data, dict) and data)
    except (json.JSONDecodeError, AttributeError):
        return False


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
            print(f"\nLoading existing data from processed file: {
                  processed_file}")
            with open(processed_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    existing_rows.append(row)
                    linkedin_url = row.get('company_linkedin_url', '').strip()
                    if linkedin_url and has_valid_data(row.get('full_json')):
                        processed_data[linkedin_url] = row
                     #   print(f"Found existing data for: {linkedin_url}")
            print(f"Loaded {len(processed_data)} existing company records")
        else:
            print(f"Processed file not found: {processed_file}")
        return processed_data, fieldnames, existing_rows
    except Exception as e:
        print(f"Error loading processed data: {e}")
        return {}, None, []


def load_interim_file(output_csv):
    """Load existing interim file data"""
    interim_data = {}
    if Path(output_csv).exists():
        with open(output_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                linkedin_url = row.get('company_linkedin_url', '').strip()
                if linkedin_url and has_valid_data(row.get('linkedin_json')):
                    interim_data[linkedin_url] = row
    return interim_data


async def save_interim_file(output_csv, fieldnames, rows):
    """Save current state to interim file"""
    with open(output_csv, "w", newline="", encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


async def fetch_company_data(session, linkedin_url):
    """Fetch company data from Scrapin API for a given LinkedIn URL."""
    async with limiter:
        try:
            encoded_url = urllib.parse.quote(linkedin_url, safe='')
            url = f"https://api.scrapin.io/enrichment/company?apikey={
                SCRAPIN_API_KEY}&linkedInUrl={encoded_url}"

            async with session.get(url) as response:
                response_text = await response.text(encoding='utf-8')
                print(f"\nFetching data from ScrapIn for: {linkedin_url}")
                print(f"Response status: {response.status}")

                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        if data and isinstance(data, dict):
                            print("Successfully retrieved company data")
                            return data
                        else:
                            print("No valid company data in response")
                            return None
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON response: {e}")
                        return None
                else:
                    print(f"API error: {response.status} - {response_text}")
                    return None
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None


async def process_single_company(session, row, interim_data, processed_data, fieldnames, output_csv, file_lock, all_rows):
    """Process a single company, using existing data if available."""
    linkedin_url = row['company_linkedin_url'].strip()
    print(f"\nRetrieving: {linkedin_url}")

    # Check processed data first
    if linkedin_url in processed_data:
        print(f"Found URL in processed data: {linkedin_url}")
        processed_row = processed_data[linkedin_url]
        if has_valid_data(processed_row.get('full_json')):
            print("Using existing processed data")
            row['linkedin_json'] = processed_row['full_json']
            async with file_lock:
                await save_interim_file(output_csv, fieldnames, all_rows)
            return True
        else:
            print("Processed data exists but invalid")

    # Check existing JSON in current row
    existing_json = row.get('linkedin_json', '')
    if has_valid_data(existing_json):
        print("Using existing JSON data from current row")
        async with file_lock:
            await save_interim_file(output_csv, fieldnames, all_rows)
        return True

    # Only fetch new data if no existing data found
    print(f"\nNo existing data found for: {linkedin_url}")
    response = await fetch_company_data(session, linkedin_url)
    if response:
        company_data = response.get('company') if isinstance(
            response, dict) and 'company' in response else response
        row['linkedin_json'] = json.dumps(company_data, ensure_ascii=False)
        print(f"Successfully processed: {row['company_name']}")
        async with file_lock:
            await save_interim_file(output_csv, fieldnames, all_rows)
        return True

    print(f"\nNo data found for: {linkedin_url}")
    row['linkedin_json'] = json.dumps({}, ensure_ascii=False)
    async with file_lock:
        await save_interim_file(output_csv, fieldnames, all_rows)
    return False


async def process_csv(input_csv, output_csv, processed_file=None):
    """Process CSV file using existing data where possible."""
    print(f"\nProcessing CSV file: {input_csv}")

    # Load existing processed and interim data
    processed_data, _, _ = load_processed_data(processed_file)
    interim_data = load_interim_file(output_csv)

    # Read input CSV
    with open(input_csv, "r", encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)
        print(f"Found {len(rows)} companies to process")

    # Define fieldnames
    fieldnames = ['company_linkedin_url', 'company_name', 'linkedin_json']

    # Lock for synchronizing file writes
    file_lock = asyncio.Lock()

    # Configure session with increased concurrent connections
    async with ClientSession(
        timeout=ClientTimeout(total=300),
        # Increased from 5 to 30 since company rate limit is higher
        connector=TCPConnector(limit=30)
    ) as session:
        tasks = []
        for row in rows:
            task = process_single_company(
                session, row, interim_data, processed_data, fieldnames, output_csv, file_lock, rows)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        success_count = sum(1 for r in results if r is True)

    total_records = len(rows)
    failed_count = total_records - success_count

    print(f"\nProcessing complete:")
    print(f"Total records: {total_records}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Results saved to: {output_csv}")


async def main():
    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python get_companies.py <input_csv>")
        sys.exit(1)

    input_csv = sys.argv[1]
    input_path = Path(input_csv)

    # If file is already in interim directory, don't create nested interim
    if input_path.parent.name == "interim":
        output_csv = input_path.parent / \
            f"{input_path.stem.replace(
                '_withLinkedInData', '')}_withLinkedInData.csv"
    else:
        output_csv = input_path.parent / "interim" / \
            f"{input_path.stem}_withLinkedInData.csv"
        # Create interim directory if needed
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get company name from current directory (we're always run from company dir)
    company_name = Path.cwd().name
    processed_file = Path("processed") / \
        f"{company_name}_companies_processed.csv"

    print(f"\nLooking for processed data in: {processed_file}")
    await process_csv(input_csv, str(output_csv), str(processed_file))


if __name__ == "__main__":
    asyncio.run(main())
