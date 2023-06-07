// Setting subscription as scope
targetScope = 'subscription'

// Parameters
@description('Name of the environment')
@allowed([
  'dev'
  'test'
  'uat'
  'prod'
])
param Environ string = 'dev'

@description('provide a 2-13 character prefix for all resources.')
@minLength(2)
@maxLength(13)
param ResourcePrefix string

@description('Azure location where the resources should be created')
@allowed([
  'westeurope'
  'eastus'
  'southcentralus'
])
param location string = 'westeurope'

@description('The SKU of the search service you want to create. E.g. free or standard')
@allowed([
  'free'
  'basic'
  'standard'
  'standard2'
  'standard3'
])
param AzureCognitiveSearchSku string = 'standard'

@description('The pricing tier for the App Service plan')
@allowed([
  'F1'
  'D1'
  'B1'
  'B2'
  'B3'
  'S1'
  'S2'
  'S3'
  'P1'
  'P2'
  'P3'
  'P4'
])
param HostingPlanSku string = 'B3'

@description('Do you want to enable Azure Translator?')
@allowed([
  true
  false
])
param EnableTranslator bool = true

@description('Azure AD Application Client Id')
param AADClientId string

@description('Azure AD Tenant Id')
param AADTenantId string

@description('Scope of Azure AD Client Application')
param AADClientScope string

@description('Website URL to redirect to after Azure AD Authentication. Leave it blank if you want to redirect to the SWA page')
param AADRedirectURL string = ''

@description('Id of the Azure AD Security Group to which general users belong')
param AADRegularUsersGroup string

@description('Id of the Azure AD Security Group to which admin users belong')
param AADAdminUsersGroup string

@description('URL of Azure OpenAI Service Endpoint')
param OpenAIEndpoint string

@description('Azure OpenAI Service API Key')
@secure()
param OpenAIKey string

@description('OpenAI Engine')
param OpenAIEngine string = 'gpt-35-turbo'

@description('OpenAI Deployment Type. Text for an Instructions based deployment (text-davinci-003). Chat for a Chat based deployment (gpt-35-turbo or gpt-4-32k or gpt-4).')
@allowed([
  'Chat'
  'Text'
])
param OpenAIDeploymentType string = 'Chat'

@description('OpenAI Embeddings Engine for Documents')
param OpenAIEmbeddingsEngineDoc string = 'text-embedding-ada-002'

@description('OpenAI Embeddings Engine for Queries')
param OpenAIEmbeddingsEngineQuery string = 'text-embedding-ada-002'

@description('Endpoint for container registry where the web app image is stored (e.g. examplereg.azurecr.io/qnawebapp:latest)')
param WebappContainerImage string

@description('Endpoint for container registry where the batch process image is stored (e.g. examplereg.azurecr.io/qnabatchprocess:latest)')
param BatchProcessContainerImage string

@description('Do you use ACR to store your container image?')
@allowed([
  true
  false
])
param EnableAcrPull bool = true

// Local variables
var CustomAcrPullRoleName = '${ResourcePrefix}-acr-pull-role'

// Create the resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'aoai-qna-test-rg'
  location: location
  tags: {
    Purpose: 'AOAI-QnA-App'
    Environment: Environ
  }
}

// Create a custome role to give read access to ACR pull
var roleDefId = guid(CustomAcrPullRoleName, subscription().id, location)
resource CustomAcrPullRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: roleDefId
  properties: {
    assignableScopes: [
      subscription().id
    ]
    description: 'Custom Role to allow ACR Pull images'
    permissions: [
      {
        actions: [
          'Microsoft.ContainerRegistry/registries/pull/read'
        ]
      }
    ]
    roleName: CustomAcrPullRoleName
    type: 'customRole'
  }
}

// Create the Private ChatGPT Application using module
module AOAIQnABot './aoai-qna-infra.bicep' = {
  name: 'aoai-qna-infra'
  scope: rg    // Deployed in the scope of resource group we created above
  params: {
    Environ: Environ
    ResourcePrefix: ResourcePrefix
    location: location
    AzureCognitiveSearchSku: AzureCognitiveSearchSku
    HostingPlanSku: HostingPlanSku
    EnableTranslator: EnableTranslator
    AADClientId: AADClientId
    AADTenantId: AADTenantId
    AADClientScope: AADClientScope
    AADRedirectURL: AADRedirectURL
    AADRegularUsersGroup: AADRegularUsersGroup
    AADAdminUsersGroup: AADAdminUsersGroup
    OpenAIEndpoint: OpenAIEndpoint
    OpenAIKey: OpenAIKey
    OpenAIEngine: OpenAIEngine
    OpenAIDeploymentType: OpenAIDeploymentType
    OpenAIEmbeddingsEngineDoc: OpenAIEmbeddingsEngineDoc
    OpenAIEmbeddingsEngineQuery: OpenAIEmbeddingsEngineQuery
    WebappContainerImage: WebappContainerImage
    BatchProcessContainerImage: BatchProcessContainerImage
    EnableAcrPull: EnableAcrPull
    CustomRoleDefId: CustomAcrPullRole.id
  }
}

output ChatAppUrl string = AOAIQnABot.outputs.ChatAppUrl
