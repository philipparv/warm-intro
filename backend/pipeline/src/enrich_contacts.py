#!/usr/bin/env python3
import sys
import pandas as pd
from thefuzz import fuzz
import logging
import argparse
import os
import urllib.parse
import json
import unicodedata


def setup_logging():
    """Configure logging for the script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def normalize_for_comparison(name):
    """
    Normalize a name for comparison purposes only.
    The original name in the data will be preserved.
    """
    if pd.isna(name):
        return ""

    # Convert to string, lowercase, and strip spaces
    name = str(name).lower().strip()

    # URL decode any encoded characters
    name = urllib.parse.unquote(name)

    # Remove any zero-width characters and other invisible characters
    name = ''.join(c for c in name if c.isprintable())

    # Remove periods from initials
    name = name.replace('.', '')

    # Normalize unicode characters (e.g., convert é to e)
    name = unicodedata.normalize('NFKD', name).encode(
        'ASCII', 'ignore').decode('ASCII')

    # Keep only letters and spaces
    normalized = ''.join(c for c in name if c.isalpha() or c.isspace())

    return normalized.strip()


def calculate_name_match_score(base_first, base_last, enrich_first, enrich_last):
    """
    Calculate match score with special handling for initials and short names
    """
    # Handle single-letter last names (likely initials)
    if len(base_last) == 1:
        # If enrichment last name starts with the same letter, consider it a potential match
        if enrich_last.startswith(base_last):
            last_score = 95  # High score but not perfect
        else:
            last_score = 0
    else:
        last_score = fuzz.ratio(base_last, enrich_last)

    # Calculate first name score
    if len(base_first) == 1:
        # If it's an initial, check if enrichment name starts with it
        if enrich_first.startswith(base_first):
            first_score = 95
        else:
            first_score = 0
    else:
        first_score = fuzz.ratio(base_first, enrich_first)

    # For very short names, also consider partial ratio
    if len(base_first) <= 2 or len(base_last) <= 2:
        partial_first = fuzz.partial_ratio(base_first, enrich_first)
        partial_last = fuzz.partial_ratio(base_last, enrich_last)
        first_score = max(first_score, partial_first)
        last_score = max(last_score, partial_last)

    return first_score, last_score


def find_best_match(row, enrichment_df, threshold=95):
    """
    Find the best matching row in enrichment_df for the given row
    using fuzzy string matching on first and last names
    """
    first_name = normalize_for_comparison(row['First Name'])
    last_name = normalize_for_comparison(row['Last Name'])

    if not first_name or not last_name:
        logging.debug(f"Skipping row with incomplete name: {
                      row['First Name']} {row['Last Name']}")
        return None

    best_match = None
    best_score = 0

    # Filter out rows with empty names
    valid_rows = []
    for _, enrich_row in enrichment_df.iterrows():
        if pd.notna(enrich_row['FirstName']) and pd.notna(enrich_row['LastName']):
            first = str(enrich_row['FirstName']).strip()
            last = str(enrich_row['LastName']).strip()
            if first and last:  # Check if non-empty after stripping
                # Convert Series to dict to avoid pandas comparison issues
                valid_rows.append(enrich_row.to_dict())

    for enrich_row in valid_rows:
        enrich_first = normalize_for_comparison(str(enrich_row['FirstName']))
        enrich_last = normalize_for_comparison(str(enrich_row['LastName']))

        if not enrich_first or not enrich_last:
            continue

        # Calculate name match scores with special handling
        first_score, last_score = calculate_name_match_score(
            first_name, last_name, enrich_first, enrich_last)

        # Both names should match well
        combined_score = (first_score + last_score) / 2

        # Log all potential matches for debugging
        if combined_score > 70:  # Only log somewhat close matches
            logging.debug(f"Comparing {row['First Name']} {row['Last Name']} ({first_name} {last_name}) with " +
                          f"{enrich_row['FirstName']} {enrich_row['LastName']} ({enrich_first} {enrich_last}): " +
                          f"score={combined_score} (first={first_score}, last={last_score})")

        if combined_score > best_score and combined_score >= threshold:
            best_score = combined_score
            best_match = enrich_row
            logging.info(f"Found match: {row['First Name']} {row['Last Name']} -> {
                         enrich_row['FirstName']} {enrich_row['LastName']} (score: {combined_score})")

    if not best_match and best_score > 0:
        logging.debug(f"Best match for {row['First Name']} {
                      row['Last Name']} had score {best_score}, below threshold {threshold}")

    return best_match


def enrich_dataframe(base_df, enrichment_df):
    """
    Enrich the base dataframe with email and phone information 
    from the enrichment dataframe, always creating new columns with _enriched suffix
    """
    # Initialize new columns with _enriched suffix
    base_df['Email_enriched'] = None
    base_df['PhoneNumbers_enriched'] = None

    enriched_count = 0
    total_count = len(base_df)

    for idx, row in base_df.iterrows():
        match = find_best_match(row, enrichment_df)

        if match is not None:
            # Add email information to new column
            if 'Emails' in match and pd.notna(match['Emails']):
                base_df.at[idx, 'Email_enriched'] = match['Emails']

            # Add phone information to new column
            if 'PhoneNumbers' in match and pd.notna(match['PhoneNumbers']):
                base_df.at[idx, 'PhoneNumbers_enriched'] = match['PhoneNumbers']

            enriched_count += 1

    logging.info(f"Enrichment rate: {
                 enriched_count}/{total_count} ({(enriched_count/total_count)*100:.1f}%)")
    return base_df, enriched_count


def get_output_filename(input_path):
    """Generate output filename in the same directory as the input file"""
    directory = os.path.dirname(input_path)
    filename = os.path.basename(input_path)
    base, ext = os.path.splitext(filename)
    new_filename = f"{base}_withContacts{ext}"
    return os.path.join(directory, new_filename)


def decode_names(df):
    """Decode URL-encoded characters in name columns"""
    for col in ['First Name', 'Last Name']:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: urllib.parse.unquote(str(x)) if pd.notna(x) else x)
    return df


def clean_linkedin_data(df):
    """Clean and prepare LinkedIn data for processing"""
    # Ensure First Name and Last Name columns exist
    if 'First Name' not in df.columns or 'Last Name' not in df.columns:
        logging.error(
            "Required columns 'First Name' and 'Last Name' not found in input file")
        sys.exit(1)

    # URL decode names
    df = decode_names(df)

    # Remove any zero-width characters and other invisible characters
    for col in ['First Name', 'Last Name']:
        df[col] = df[col].apply(lambda x: ''.join(
            c for c in str(x) if c.isprintable()) if pd.notna(x) else x)

    return df


def main():
    parser = argparse.ArgumentParser(
        description='Enrich a processed people CSV file with contact information from another CSV file')
    parser.add_argument(
        'base_file', help='Path to the processed people CSV file to be enriched')
    parser.add_argument('enrichment_file',
                        help='Path to the CSV file containing enrichment data')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Read the CSV files with UTF-8 encoding
        logging.info(f"Reading base file: {args.base_file}")
        base_df = pd.read_csv(args.base_file, encoding='utf-8')

        logging.info(f"Reading enrichment file: {args.enrichment_file}")
        enrichment_df = pd.read_csv(args.enrichment_file, encoding='utf-8')

        # Clean and prepare the LinkedIn data
        base_df = clean_linkedin_data(base_df)

        # Verify required columns exist
        required_base_columns = ['First Name', 'Last Name']
        required_enrich_columns = ['FirstName',
                                   'LastName', 'Emails', 'PhoneNumbers']

        missing_base_cols = [
            col for col in required_base_columns if col not in base_df.columns]
        if missing_base_cols:
            raise ValueError(
                f"Missing required columns in base file: {', '.join(missing_base_cols)}")

        missing_enrich_cols = [
            col for col in required_enrich_columns if col not in enrichment_df.columns]
        if missing_enrich_cols:
            raise ValueError(
                f"Missing required columns in enrichment file: {', '.join(missing_enrich_cols)}")

        # Log some sample data for debugging
        logging.debug("Sample base data:")
        logging.debug(base_df[['First Name', 'Last Name']].head())
        logging.debug("\nSample enrichment data:")
        logging.debug(enrichment_df[['FirstName', 'LastName']].head())

        # Perform enrichment
        logging.info("Starting enrichment process...")
        enriched_df, enriched_count = enrich_dataframe(base_df, enrichment_df)

        # Save the result with UTF-8 encoding
        output_file = get_output_filename(args.base_file)
        enriched_df.to_csv(output_file, index=False, encoding='utf-8')
        logging.info(
            f"Enrichment complete. {enriched_count} records were enriched.")
        logging.info(f"Enriched file saved to: {output_file}")

    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logging.error(str(e))
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
