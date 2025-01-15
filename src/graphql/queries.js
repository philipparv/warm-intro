/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const getConnection = /* GraphQL */ `
  query GetConnection($id: ID!) {
    getConnection(id: $id) {
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
export const listConnections = /* GraphQL */ `
  query ListConnections(
    $filter: ModelConnectionFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listConnections(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
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
      nextToken
      __typename
    }
  }
`;
export const getCompany = /* GraphQL */ `
  query GetCompany($id: ID!) {
    getCompany(id: $id) {
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
export const listCompanies = /* GraphQL */ `
  query ListCompanies(
    $filter: ModelCompanyFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listCompanies(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
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
      nextToken
      __typename
    }
  }
`;
