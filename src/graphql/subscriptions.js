/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const onCreateConnection = /* GraphQL */ `
  subscription OnCreateConnection(
    $filter: ModelSubscriptionConnectionFilterInput
  ) {
    onCreateConnection(filter: $filter) {
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
export const onUpdateConnection = /* GraphQL */ `
  subscription OnUpdateConnection(
    $filter: ModelSubscriptionConnectionFilterInput
  ) {
    onUpdateConnection(filter: $filter) {
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
export const onDeleteConnection = /* GraphQL */ `
  subscription OnDeleteConnection(
    $filter: ModelSubscriptionConnectionFilterInput
  ) {
    onDeleteConnection(filter: $filter) {
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
export const onCreateCompany = /* GraphQL */ `
  subscription OnCreateCompany($filter: ModelSubscriptionCompanyFilterInput) {
    onCreateCompany(filter: $filter) {
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
export const onUpdateCompany = /* GraphQL */ `
  subscription OnUpdateCompany($filter: ModelSubscriptionCompanyFilterInput) {
    onUpdateCompany(filter: $filter) {
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
export const onDeleteCompany = /* GraphQL */ `
  subscription OnDeleteCompany($filter: ModelSubscriptionCompanyFilterInput) {
    onDeleteCompany(filter: $filter) {
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
