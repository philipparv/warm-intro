/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const createConnection = /* GraphQL */ `
  mutation CreateConnection(
    $input: CreateConnectionInput!
    $condition: ModelConnectionConditionInput
  ) {
    createConnection(input: $input, condition: $condition) {
      id
      companyName
      contactName
      linkedinURL
      firstName
      lastName
      email
      position
      connectedOn
      contact
      educationInstitutions
      pastCompanies
      linkedinJSON
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const updateConnection = /* GraphQL */ `
  mutation UpdateConnection(
    $input: UpdateConnectionInput!
    $condition: ModelConnectionConditionInput
  ) {
    updateConnection(input: $input, condition: $condition) {
      id
      companyName
      contactName
      linkedinURL
      firstName
      lastName
      email
      position
      connectedOn
      contact
      educationInstitutions
      pastCompanies
      linkedinJSON
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const deleteConnection = /* GraphQL */ `
  mutation DeleteConnection(
    $input: DeleteConnectionInput!
    $condition: ModelConnectionConditionInput
  ) {
    deleteConnection(input: $input, condition: $condition) {
      id
      companyName
      contactName
      linkedinURL
      firstName
      lastName
      email
      position
      connectedOn
      contact
      educationInstitutions
      pastCompanies
      linkedinJSON
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const createCompany = /* GraphQL */ `
  mutation CreateCompany(
    $input: CreateCompanyInput!
    $condition: ModelCompanyConditionInput
  ) {
    createCompany(input: $input, condition: $condition) {
      id
      companyName
      companyLinkedInURL
      websiteURL
      industry
      specialties
      employeeCount
      city
      geographicArea
      postalCode
      founded
      tagline
      description
      logoURL
      fullJSON
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const updateCompany = /* GraphQL */ `
  mutation UpdateCompany(
    $input: UpdateCompanyInput!
    $condition: ModelCompanyConditionInput
  ) {
    updateCompany(input: $input, condition: $condition) {
      id
      companyName
      companyLinkedInURL
      websiteURL
      industry
      specialties
      employeeCount
      city
      geographicArea
      postalCode
      founded
      tagline
      description
      logoURL
      fullJSON
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const deleteCompany = /* GraphQL */ `
  mutation DeleteCompany(
    $input: DeleteCompanyInput!
    $condition: ModelCompanyConditionInput
  ) {
    deleteCompany(input: $input, condition: $condition) {
      id
      companyName
      companyLinkedInURL
      websiteURL
      industry
      specialties
      employeeCount
      city
      geographicArea
      postalCode
      founded
      tagline
      description
      logoURL
      fullJSON
      createdAt
      updatedAt
      __typename
    }
  }
`;
