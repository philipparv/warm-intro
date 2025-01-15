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
    """Check if JSON string contains actual person data."""
    try:
        if not json_str or json_str.strip() in ['{}', '']:
            return False
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        # Check if we have any meaningful person data
        return bool(
            isinstance(data, dict) and
            any(data.get(field) for field in [
                'firstName', 'lastName', 'positions', 'schools',
                'linkedInIdentifier', 'publicIdentifier'
            ])
        )
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
            print(f"\nReading existing processed file: {processed_file}")
            with open(processed_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    existing_rows.append(row)
                    # Handle BOM in column name
                    linkedin_url_key = next(
                        (k for k in row.keys() if k and k.lower().endswith('linkedinurl')), '')
                    linkedin_url = row.get(linkedin_url_key, '').strip()
                    if linkedin_url and has_valid_data(row.get('linkedin_json')):
                        processed_data[linkedin_url] = row
                    #    print(f"Added processed data for: {linkedin_url}")
            print(f"Loaded {len(processed_data)
                            } processed person records with valid data")
        else:
            print(f"Processed file not found: {processed_file}")
        return processed_data, fieldnames, existing_rows
    except Exception as e:
        print(f"Error loading processed data: {e}")
        return {}, None, []


def load_interim_data(interim_file):
    """Load existing data from interim file."""
    interim_data = {}
    try:
        if Path(interim_file).exists():
            with open(interim_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    linkedin_url_key = next(
                        (k for k in row.keys() if k and k.lower().endswith('linkedinurl')), '')
                    linkedin_url = row.get(linkedin_url_key, '').strip()
                    if linkedin_url and has_valid_data(row.get('linkedin_json')):
                        interim_data[linkedin_url] = row
            print(f"Loaded {len(interim_data)
                            } interim records with valid data")
        return interim_data
    except Exception as e:
        print(f"Error loading interim data: {e}")
        return {}


def append_to_processed_file(processed_file, row, fieldnames):
    """Append a single row to the processed file."""
    try:
        file_exists = Path(processed_file).exists()
        with open(processed_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        return True
    except Exception as e:
        print(f"Error appending to processed file: {e}")
        return False


async def fetch_linkedin_data(session, linked_in_url):
    """Fetch data from Scrapin API for a given LinkedIn URL."""
    async with limiter:
        try:
            encoded_url = urllib.parse.quote(linked_in_url, safe='')
            url = f"https://api.scrapin.io/enrichment/profile?apikey={
                SCRAPIN_API_KEY}&linkedInUrl={encoded_url}"

            async with session.get(url) as response:
                response_text = await response.text(encoding='utf-8')
                print(f"\nFetching data for: {linked_in_url}")
                print(f"Response status: {response.status}")

                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        person_data = data.get("person")
                        if isinstance(person_data, dict):
                            print("Successfully retrieved person data")
                            return person_data
                        else:
                            print("Invalid person data format in response")
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


async def save_interim_file(output_csv, fieldnames, rows):
    """Save current state to interim file"""
    with open(output_csv, "w", newline="", encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


async def process_single_person(session, row, interim_data, processed_data, fieldnames, output_csv, file_lock, all_rows):
    """Process a single person, using existing data if available."""
    linkedin_url_key = next(
        (k for k in row.keys() if k and k.lower().endswith('linkedinurl')), '')
    linkedin_url = row.get(linkedin_url_key, '').strip()
    print(f"\nProcessing: {linkedin_url}")

    # Check processed data first
    if linkedin_url in processed_data:
        processed_row = processed_data[linkedin_url]
        if has_valid_data(processed_row.get('linkedin_json')):
            print("Using existing processed data")
            # Copy only the linkedin_json field to preserve other fields from input
            row['linkedin_json'] = processed_row['linkedin_json']
            async with file_lock:
                await save_interim_file(output_csv, fieldnames, all_rows)
            return True
        else:
            print("Processed data exists but invalid")

    # Check interim data
    if linkedin_url in interim_data:
        print("Using existing interim data")
        interim_row = interim_data[linkedin_url]
        row.update(interim_row)
        async with file_lock:
            await save_interim_file(output_csv, fieldnames, all_rows)
        return True

    # Check existing JSON in current row
    existing_json = row.get('linkedin_json', '')
    if has_valid_data(existing_json):
        print("Using existing JSON data from current row")
        async with file_lock:
            await save_interim_file(output_csv, fieldnames, all_rows)
        return True

    # Only fetch new data if no existing data found
    if linkedin_url:
        print("No existing data found, fetching new data")
        response = await fetch_linkedin_data(session, linkedin_url)
        if response and isinstance(response, dict):
            row['linkedin_json'] = json.dumps(response, ensure_ascii=False)
            async with file_lock:
                await save_interim_file(output_csv, fieldnames, all_rows)
            return True

    print("No valid data available")
    async with file_lock:
        await save_interim_file(output_csv, fieldnames, all_rows)
    return False


async def process_csv(input_csv, output_csv, processed_file=None):
    """Process CSV file using existing data where possible."""
    print(f"\nProcessing CSV file: {input_csv}")

    # Get input path
    input_path = Path(input_csv)

    print(f"\nLooking for existing processed people data in: {processed_file}")

    # Load existing processed and interim data
    processed_data, _, _ = load_processed_data(processed_file)
    interim_data = load_interim_data(output_csv)

    # Read input CSV
    with open(input_csv, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        input_fieldnames = reader.fieldnames
        rows = list(reader)

    # Define fieldnames
    fieldnames = (
        input_fieldnames +
        ['linkedin_json'] if 'linkedin_json' not in input_fieldnames else input_fieldnames
    )

    # Lock for synchronizing file writes
    file_lock = asyncio.Lock()

    # Configure session for any new data fetching needed
    async with ClientSession(
        timeout=ClientTimeout(total=300),
        connector=TCPConnector(limit=20)
    ) as session:
        tasks = []
        for row in rows:
            task = process_single_person(
                session, row, interim_data, processed_data, fieldnames, output_csv, file_lock, rows)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        success_count = sum(1 for r in results if r is True)

    total_records = len(rows)
    failed_count = total_records - success_count

    print(f"\nProcessing complete:")
    print(f"Total records: {total_records}")
    print(f"Successful (including existing data): {success_count}")
    print(f"Failed or empty: {failed_count}")
    print(f"Results saved to: {output_csv}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <input_csv>")
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
    processed_file = Path("processed") / f"{company_name}_people_processed.csv"

    print(f"\nLooking for existing processed data in: {processed_file}")
    await process_csv(input_csv, str(output_csv), str(processed_file))


if __name__ == "__main__":
    asyncio.run(main())
