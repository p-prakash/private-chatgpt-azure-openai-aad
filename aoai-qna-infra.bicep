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

param CustomRoleDefId string

// Variables
var newGuid = guid(resourceGroup().id, deployment().name)
var AzureCognitiveSearchName = '${ResourcePrefix}-search'
var HostingPlanName = '${ResourcePrefix}-plan'
var StorageAccountName = '${toLower(ResourcePrefix)}str'
var WebsiteName = '${ResourcePrefix}-site'
var FunctionName = '${ResourcePrefix}-batchfunc'
var ApplicationInsightsName = '${ResourcePrefix}-appinsights'
var FormRecognizerName = '${ResourcePrefix}-formrecog'
var TranslatorName = '${ResourcePrefix}-translator'
var CustomAcrPullRoleName = '${ResourcePrefix}-acr-pull-role'
var BlobContainerName = 'documents'
var QueueName = 'doc-processing'
var ClientKey = '${uniqueString(guid(resourceGroup().id, subscription().subscriptionId, deployment().name))}${newGuid}Tg2%'
var UserAssignedIdentityName = '${ResourcePrefix}-identity'
var tagName = {
  Purpose:'AOAI-QnA-App'
  Environment: Environ
}

// Create a user assigned identtiy
resource UserAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31'  = if (EnableAcrPull) {
  name: UserAssignedIdentityName
  location: location
}

// Create custom role assignment
resource CustomAcrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (EnableAcrPull) {
  name: guid(CustomAcrPullRoleName, deployment().name)
  properties: {
    roleDefinitionId: CustomRoleDefId
    // subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: UserAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Create Azure Cognitive Search
resource AzureCognitiveSearch 'Microsoft.Search/searchServices@2020-08-01' = {
  name: AzureCognitiveSearchName
  location: location
  sku: {
    name: AzureCognitiveSearchSku
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
  }
  tags: tagName
}

// Create Form Recognizer
resource FormRecognizer 'Microsoft.CognitiveServices/accounts@2022-12-01' = {
  name: FormRecognizerName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'FormRecognizer'
  identity: {
    type: 'None'
  }
  properties: {
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: 'Enabled'
  }
  tags: tagName
}

// Create Translator if it's enabled
resource Translator 'Microsoft.CognitiveServices/accounts@2022-12-01' = if (EnableTranslator) {
  name: TranslatorName
  location: location
  sku: {
    name: 'S1'
  }
  kind: 'TextTranslation'
  identity: {
    type: 'None'
  }
  properties: {
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: 'Enabled'
  }
  tags: tagName
}

// Create App Service Plan
resource HostingPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: HostingPlanName
  location: location
  sku: {
    name: HostingPlanSku
  }
  properties: {
    reserved: true
  }
  kind: 'linux'
  tags: tagName
}

// Create Website using App Service
resource Website 'Microsoft.Web/sites@2022-03-01' = {
  name: WebsiteName
  location: location
  identity: ((EnableAcrPull) ? {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${UserAssignedIdentity.id}': {}
    }
  }: {})
  properties: {
    serverFarmId: HostingPlan.id
    siteConfig: {
      acrUseManagedIdentityCreds: ((EnableAcrPull) ? true : false)
      acrUserManagedIdentityID: ((EnableAcrPull) ? UserAssignedIdentity.properties.clientId : null)
      linuxFxVersion: 'DOCKER|${WebappContainerImage}'
    }
  }
  tags: tagName
}

// Create a Storage Account
resource StorageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: StorageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_GRS'
  }
  tags: tagName
}

// Create a Blob Container in the above Storage Account
resource StorageAccountBlobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  name: '${StorageAccountName}/default/${BlobContainerName}'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    StorageAccount
  ]
}

// Create a Queue Service in the above Storage Account
resource StorageAccountQueue 'Microsoft.Storage/storageAccounts/queueServices@2022-09-01' = {
  parent: StorageAccount
  name: 'default'
  properties: {
    cors: {
      corsRules: []
    }
  }
}

// Create a Queue for document processing in the above Queue Service
resource StorageAccountDocProcessingQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2022-09-01' = {
  parent: StorageAccountQueue
  name: QueueName
  properties: {
    metadata: {}
  }
}

// Create a Queue for document processing poison in the above Queue Service
resource StorageAccountDocProcessingPoisonQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2022-09-01' = {
  parent: StorageAccountQueue
  name: '${QueueName}-poison'
  properties: {
    metadata: {}
  }
}

// Create an Application Insights instance
resource ApplicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: ApplicationInsightsName
  location: location
  properties: {
    Application_Type: 'web'
  }
  kind: 'web'
  tags: tagName
}

// Create an Azure Function App
resource ProcessingFunction 'Microsoft.Web/sites@2022-03-01' = {
  name: FunctionName
  kind: 'functionapp,linux'
  location: location
  identity: ((EnableAcrPull) ? {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${UserAssignedIdentity.id}': {}
    }
  }: {})
  properties: {
    siteConfig: {
      acrUseManagedIdentityCreds: ((EnableAcrPull) ? true : false)
      acrUserManagedIdentityID: ((EnableAcrPull) ? UserAssignedIdentity.properties.clientId : null)
      appSettings: [
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: ApplicationInsights.properties.InstrumentationKey
        }
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${StorageAccountName};AccountKey=${StorageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'OPENAI_ENGINE'
          value: OpenAIEngine
        }
        {
          name: 'OPENAI_DEPLOYMENT_TYPE'
          value: OpenAIDeploymentType
        }
        {
          name: 'OPENAI_EMBEDDINGS_ENGINE_DOC'
          value: OpenAIEmbeddingsEngineDoc
        }
        {
          name: 'OPENAI_EMBEDDINGS_ENGINE_QUERY'
          value: OpenAIEmbeddingsEngineQuery
        }
        {
          name: 'OPENAI_API_BASE'
          value: OpenAIEndpoint
        }
        {
          name: 'OPENAI_API_KEY'
          value: OpenAIKey
        }
        {
          name: 'BLOB_ACCOUNT_NAME'
          value: StorageAccountName
        }
        {
          name: 'BLOB_ACCOUNT_KEY'
          value: StorageAccount.listKeys().keys[0].value
        }
        {
          name: 'BLOB_CONTAINER_NAME'
          value: BlobContainerName
        }
        {
          name: 'FORM_RECOGNIZER_ENDPOINT'
          value: 'https://${location}.api.cognitive.microsoft.com/'
        }
        {
          name: 'FORM_RECOGNIZER_KEY'
          value: FormRecognizer.listKeys().key1
        }
        {
          name: 'VECTOR_STORE_TYPE'
          value: 'AzureSearch'
        }
        {
          name: 'AZURE_SEARCH_SERVICE_NAME'
          value: 'https://${AzureCognitiveSearchName}.search.windows.net'
        }
        {
          name: 'AZURE_SEARCH_ADMIN_KEY'
          value: AzureCognitiveSearch.listAdminKeys().primaryKey
        }
        {
          name: 'TRANSLATE_ENDPOINT'
          value: ((EnableTranslator) ? 'https://api.cognitive.microsofttranslator.com/' : '')
        }
        {
          name: 'TRANSLATE_KEY'
          value: ((EnableTranslator) ? Translator.listKeys().key1 : '')
        }
        {
          name: 'TRANSLATE_REGION'
          value: ((EnableTranslator) ? location : '')
        }
        {
          name: 'QUEUE_NAME'
          value: QueueName
        }
      ]
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
        ]
      }
      use32BitWorkerProcess: false
      linuxFxVersion: 'DOCKER|${BatchProcessContainerImage}'
      appCommandLine: ''
      alwaysOn: true
    }
    serverFarmId: HostingPlan.id
    clientAffinityEnabled: false
    httpsOnly: true
  }
  tags: tagName
}

// Create a Function Key for the above Function App
resource ProcessingFunctionKey 'Microsoft.Web/sites/host/functionKeys@2022-03-01' = {
  name: '${FunctionName}/default/clientKey'
  properties: {
    name: 'ClientKey'
    value: ClientKey
  }
  dependsOn: [
    ProcessingFunction
    WaitFunctionDeploymentSection
  ]
}

// Configure App Settings for the Website
resource WebsiteAppSettings 'Microsoft.Web/sites/config@2021-03-01' = {
  parent: Website
  name: 'appsettings'
  kind: 'string'
  properties: {
    AAD_ClietnId: AADClientId
    AAD_Authority: '${environment().authentication.loginEndpoint}${AADTenantId}'
    AAD_Redirect_URL: ((AADRedirectURL == '') ? 'https://${Website.properties.hostNames[0]}' : AADRedirectURL)
    AAD_Scope: AADClientScope
    AAD_General_SG: AADRegularUsersGroup
    AAD_Admin_SG: AADAdminUsersGroup
    APPINSIGHTS_INSTRUMENTATIONKEY: ApplicationInsights.properties.InstrumentationKey
    OPENAI_ENGINE: OpenAIEngine
    OPENAI_DEPLOYMENT_TYPE: OpenAIDeploymentType
    OPENAI_EMBEDDINGS_ENGINE_DOC: OpenAIEmbeddingsEngineDoc
    OPENAI_EMBEDDINGS_ENGINE_QUERY: OpenAIEmbeddingsEngineQuery
    VECTOR_STORE_TYPE: 'AzureSearch'
    AZURE_SEARCH_SERVICE_NAME: 'https://${AzureCognitiveSearchName}.search.windows.net'
    AZURE_SEARCH_ADMIN_KEY: AzureCognitiveSearch.listAdminKeys().primaryKey
    OPENAI_API_BASE: OpenAIEndpoint
    OPENAI_API_KEY: OpenAIKey
    BLOB_ACCOUNT_NAME: StorageAccountName
    BLOB_ACCOUNT_KEY: StorageAccount.listKeys().keys[0].value
    BLOB_CONTAINER_NAME: BlobContainerName
    FORM_RECOGNIZER_ENDPOINT: 'https://${location}.api.cognitive.microsoft.com/'
    FORM_RECOGNIZER_KEY: FormRecognizer.listKeys().key1
    TRANSLATE_ENDPOINT: ((EnableTranslator) ? 'https://api.cognitive.microsofttranslator.com/' : '')
    TRANSLATE_KEY:  ((EnableTranslator) ? Translator.listKeys().key1 : '')
    TRANSLATE_REGION: ((EnableTranslator) ? location : '')
    CONVERT_ADD_EMBEDDINGS_URL: 'https://${FunctionName}.azurewebsites.net/api/BatchStartProcessing?code=${ClientKey}'
  }
}

// Wait for the deployment to complete
resource WaitFunctionDeploymentSection 'Microsoft.Resources/deploymentScripts@2020-10-01' = {
  kind: 'AzurePowerShell'
  name: 'WaitFunctionDeploymentSection'
  location: location
  properties: {
    azPowerShellVersion: '3.0'
    scriptContent: 'start-sleep -Seconds 300'
    cleanupPreference: 'Always'
    retentionInterval: 'PT1H'
  }
  dependsOn: [
    ProcessingFunction
  ]
}

output ChatAppUrl string = ((AADRedirectURL == '') ? 'https://${Website.properties.hostNames[0]}' : AADRedirectURL)
