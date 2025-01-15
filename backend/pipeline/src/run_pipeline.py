#!/usr/bin/env python3
from get_people import process_csv as get_people_data
from get_companies import process_csv as fetch_company_data
from process_linkedin_companydata import process_csv as process_company_data
from extract_company_list import process_linkedin_data as extract_company_list
from process_linkedin_peopledata import process_csv as process_linkedin_data
import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path to ensure imports work from any directory
current_file = Path(__file__).resolve()
src_dir = current_file.parent
sys.path.append(str(src_dir))


def ensure_directories(base_dir):
    """Ensure interim and processed directories exist"""
    (base_dir / "interim").mkdir(exist_ok=True)
    (base_dir / "processed").mkdir(exist_ok=True)


async def run_pipeline(input_csv):
    """
    Run the complete data processing pipeline:
    1. Fetch LinkedIn profile data for each person
    2. Process the LinkedIn data to extract companies and education
    3. Extract unique company list
    4. Fetch detailed company information
    """
    try:
        input_path = Path(input_csv).resolve()  # Get absolute path
        base_dir = input_path.parent
        base_name = base_dir.name  # Use containing folder name as base name

        # Ensure required directories exist
        ensure_directories(base_dir)

        print("\n=== Starting Data Processing Pipeline ===\n")
        print(f"Base directory: {base_dir}")
        print(f"Base name: {base_name}")

        # Define paths for interim and processed files
        interim_dir = base_dir / "interim"
        processed_dir = base_dir / "processed"

        # Step 1: Fetch LinkedIn profile data
        print("Step 1: Fetching LinkedIn people profile data...")
        people_data_csv = interim_dir / \
            f"{input_path.stem}_withLinkedInData.csv"
        processed_people_file = processed_dir / \
            f"{base_name}_people_processed.csv"
        await get_people_data(
            input_csv=str(input_path),
            output_csv=str(people_data_csv),
            # Pass processed file path
            processed_file=str(processed_people_file)
        )
        print("\nStep 1 Complete: LinkedIn people profile data fetched\n")

        # Step 2: Process LinkedIn data
        print("Step 2: Processing LinkedIn data...")
        process_linkedin_data(
            input_file=str(people_data_csv),
            output_file=str(processed_people_file),
            # Pass processed file path like in Step 1
            processed_file=str(processed_people_file)
        )
        print("\nStep 2 Complete: LinkedIn data processed\n")

        # Step 3: Extract company list
        print("Step 3: Extracting company list...")
        company_list_csv = interim_dir / f"{input_path.stem}_company-list.csv"
        extract_company_list(
            input_file=str(people_data_csv),
            output_file=str(company_list_csv)
        )
        print("\nStep 3 Complete: Company list extracted\n")

        # Step 4: Fetch company information
        print("Step 4: Fetching company information...")
        processed_companies_file = processed_dir / \
            f"{base_name}_companies_processed.csv"
        # Step 4a: Fetch company information
        company_data_csv = interim_dir / \
            f"{input_path.stem}_company-list_withLinkedInData.csv"
        await fetch_company_data(
            input_csv=str(company_list_csv),
            output_csv=str(company_data_csv),
            # Pass processed file path
            processed_file=str(processed_companies_file)
        )
        print("\nStep 4a Complete: Company information fetched\n")

        # Step 4b: Process company information
        print("Step 4b: Processing company information...")
        process_company_data(
            input_file=str(company_data_csv),
            output_file=str(processed_companies_file)
        )
        print("\nStep 4b Complete: Company information processed\n")

        print("=== Pipeline Complete ===")
        print(f"Final output files:")
        print(f"People data: {processed_people_file}")
        print(f"Company data: {processed_companies_file}")

    except Exception as e:
        print(f"\nError in pipeline: {str(e)}")
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python run_pipeline.py <input_csv>")
        print("Input CSV should contain a 'LinkedinURL' column with profile URLs")
        sys.exit(1)

    input_csv = sys.argv[1]
    asyncio.run(run_pipeline(input_csv))


if __name__ == "__main__":
    main()
