import boto3
import pandas as pd
from decimal import Decimal
import numpy as np

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="us-east-2")

# DynamoDB Table Names
CONNECTIONS_TABLE_NAME = "Connections-dev"
COMPANIES_TABLE_NAME = "Companies-dev"

# Helper function to recursively convert floats to Decimal and handle invalid values
def convert_item_to_dynamodb_format(item):
    if isinstance(item, dict):
        return {key: convert_item_to_dynamodb_format(value) for key, value in item.items()}
    elif isinstance(item, list):
        return [convert_item_to_dynamodb_format(value) for value in item]
    elif isinstance(item, (float, int)):
        # Handle NaN or Infinity
        if np.isnan(item) or np.isinf(item):
            return None  # Replace with None or a default value if needed
        return Decimal(str(item))  # Convert to Decimal
    elif pd.isnull(item):  # Handle NaN for non-numeric types
        return None
    return item  # Return as-is for other types

# Load Connections Data
def load_connections(file_path):
    table = dynamodb.Table(CONNECTIONS_TABLE_NAME)
    data = pd.read_csv(file_path)

    # Replace NaN and Infinity with None in the DataFrame
    data = data.replace([np.nan, np.inf, -np.inf], None)

    for _, row in data.iterrows():
        # Derive ContactName from FirstName and LastName
        contact_name = f"{row['First Name']} {row['Last Name']}" if pd.notnull(row['First Name']) and pd.notnull(row['Last Name']) else None

        item = {
            "CompanyName": row["Company"],  # Add CompanyName as the primary key
            "ContactName": contact_name,   # Add ContactName as the sort key
            "LinkedinURL": row["LinkedinURL"],
            "FirstName": row["First Name"],
            "LastName": row["Last Name"],
            "Email": row["Email"],
            "Position": row["Position"],
            "ConnectedOn": row["Connected On"],
            "Contact": row["Contact"],
            "EducationInstitutions": row["Education Institutions"],
            "PastCompanies": row["Companies"],
            "LinkedinJSON": row["linkedin_json"],
        }
        # Convert the item to DynamoDB format
        table.put_item(Item=convert_item_to_dynamodb_format(item))
    print(f"Loaded connections data from {file_path}")

# Load Companies Data
def load_companies(file_path):
    table = dynamodb.Table(COMPANIES_TABLE_NAME)
    data = pd.read_csv(file_path)

    # Replace NaN and Infinity with None in the DataFrame
    data = data.replace([np.nan, np.inf, -np.inf], None)

    for _, row in data.iterrows():
        item = {
            "CompanyName": row["company_name"],  # Add CompanyName as the primary key
            "CompanyLinkedInURL": row["company_linkedin_url"],
            "WebsiteURL": row["website_url"],
            "Industry": row["industry"],
            "Specialties": row["specialties"],
            "EmployeeCount": row["employee_count"],
            "City": row["city"],
            "GeographicArea": row["geographic_area"],
            "PostalCode": row["postal_code"],
            "Founded": row["founded"],
            "Tagline": row["tagline"],
            "Description": row["description"],
            "LogoURL": row["logo_url"],
            "FullJSON": row["full_json"],
        }
        # Convert the item to DynamoDB format
        table.put_item(Item=convert_item_to_dynamodb_format(item))
    print(f"Loaded companies data from {file_path}")

if __name__ == "__main__":
    # Replace with the actual file paths
    connections_file = "../pipeline/Example Co_people_processed.csv"
    companies_file = "../pipeline/Example Co_companies_processed.csv"

    load_connections(connections_file)
    load_companies(companies_file)
