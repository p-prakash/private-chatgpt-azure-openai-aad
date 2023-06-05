# Build Internal & Private ChatGPT using Azure OpenAI Service

This is a modified version of [Azure OpenAI Embeddings QnA](https://github.com/ruoccofabrizio/azure-open-ai-embeddings-qna) built by [Fabrizio Ruocco](https://github.com/ruoccofabrizio).

For the overall architecture, please refer to the original repo.

## Changes from the original repo
* Added authentication and authorization using Azure AD.
    * Generic users will have access only to the chat applications
    * Admin users will have access to the admin portal to add/delete document and view indexes.  
* Created Bicep templates to deploy the application on Azure with Azure Cognitive Search.

## Prerequisites
* an existing Azure OpenAI resource with models deployments (instruction models e.g. `gpt-35-turbo`, and embeddings models e.g. `text-embedding-ada-002`)
* Azure AD tenant where Client App is registered and two Security Groups are created. Collect details about Client ID, Tenant ID, Scope, Group IDs.
* Azure Container Registry where the Docker image will be pushed.
* Azure CLI & Bicep CLI is installed in your workstation.
* Node.js 18 is installed in your workstation.
## Compiling the authentication and authorization component

Navigate to `code\msal_streamlit_authentication\frontend` folder and run the following commands:

```shell
npm install
npm run build
```

This will build the MSAL authentication and authorization component used by Streamlit. This component is built using the [OpenID Connect (OIDC) authentication component for Streamlit](https://github.com/p-prakash/private-chatgpt-azure-openai-aad) repository.

## Building the Docker images

To build locally and push to your ACR repository, run the following commands:

```shell
az acr login --name [YOUR_ACR_REPO]
docker build -t [YOUR_ACR_REPO].azurecr.io/qnawebapp:latest -f WebApp.Dockerfile .
docker push [YOUR_ACR_REPO].azurecr.io/qnawebapp:latest
docker build -t [YOUR_ACR_REPO].azurecr.io/qnabatchprocess:latest -f BatchProcess.Dockerfile .
docker push [YOUR_ACR_REPO].azurecr.io/qnabatchprocess:latest
```

To build directly on ACR
```shell
az acr login --name [YOUR_ACR_REPO]
az acr build --image [YOUR_ACR_REPO].azurecr.io/qnawebapp:latest --registry [YOUR_ACR_REPO] --file WebApp.Dockerfile .
az acr build --image [YOUR_ACR_REPO].azurecr.io/qnabatchprocess:latest --registry [YOUR_ACR_REPO] --file BatchProcess.Dockerfile .
```

## Deploy on Azure (WebApp + Batch Processing) with Azure Cognitive Search

Open the Bicep parameter file `main.parameters.json` and fill in the parameters as described in the [Environment variables](#environment-variables) section.

Then run the following commands:

```shell
az deployment sub create --location [YOUR_AZURE_LOCATION] --template-file main.bicep --parameters main.parameters.json
```

> Location can be one of `westeurope`, `eastus`, or `southcentralus`.

### Signing up for Vector Search Private Preview in Azure Cognitive Search
Azure Cognitive Search supports searching using pure vectors, pure text, or in hybrid mode where both are combined. For the vector-based cases, you'll need to sign up for Vector Search Private Preview. To sign up, please fill in this form: [https://aka.ms/VectorSearchSignUp](https://aka.ms/VectorSearchSignUp).

Preview functionality is provided under [Supplemental Terms of Use](https://azure.microsoft.com/en-us/support/legal/preview-supplemental-terms/), without a service level agreement, and isn't recommended for production workloads.

## Run everything locally in Docker (WebApp + Redis Stack + Batch Processing)

After building the docker containers as described in the previous section, copy the `.env.template` file to `.env` and fill in the parameters as described in the [Environment variables](#environment-variables) section.

Next, update the `docker-compose.yml` file with the correct Image name.

Finally run the application:

```console
docker compose up
```

Open your browser at [http://localhost:8080](http://localhost:8080)

This will spin up three Docker containers:
-   The WebApp itself
-   Redis Stack for storing the embeddings
-   Batch Processing Azure Function

NOTE: Please note that the Batch Processing Azure Function uses an Azure Storage Account for queuing the documents to process. Please create a Queue named "doc-processing" in the account used for the "AzureWebJobsStorage" env setting.

## Environment variables

Here is the explanation of the parameters:

| App Setting | Value | Note |
| --- | --- | ------------- |
|AAD_ClietnId| YOUR_AAD_CLIENT_ID | Client ID of the Azure AD App Registration|
|AAD_TenantId| YOUR_AAD_TENANT_ID | Tenant ID of the Azure AD App Registration|
|AAD_Scope| YOUR_AAD_SCOPE | Scope of the Azure AD App Registration|
|AAD_Admin_SG| YOUR_AAD_GROUP_ID_ADMIN | Group ID of the Azure AD Security Group for Admin users|
|AAD_General_SG| YOUR_AAD_GROUP_ID_USER | Group ID of the Azure AD Security Group for Generic users|
|AAD_Redirect_URL| http://localhost:8080 | Redirect URL of the Azure AD App Registration|
|OPENAI_ENGINE|gpt-35-turbo|Engine deployed in your Azure OpenAI resource. E.g. Instruction based model: text-davinci-003 or Chat based model: gpt-35-turbo or gpt-4-32k or gpt-4. Please use the deployment name and not the model name.|
|OPENAI_DEPLOYMENT_TYPE | Chat | Text for Instruction engines (text-davinci-003), <br> Chat for Chat based deployment (gpt-35-turbo or gpt-4-32k or gpt-4) |
|OPENAI_EMBEDDINGS_ENGINE_DOC | text-embedding-ada-002  | Embedding engine for documents deployed in your Azure OpenAI resource|
|OPENAI_EMBEDDINGS_ENGINE_QUERY | text-embedding-ada-002  | Embedding engine for query deployed in your Azure OpenAI resource|
|OPENAI_API_BASE | https://YOUR_AZURE_OPENAI_RESOURCE.openai.azure.com/ | Your Azure OpenAI Resource name. Get it in the [Azure Portal](https://portal.azure.com)|
|OPENAI_API_KEY| YOUR_AZURE_OPENAI_KEY | Your Azure OpenAI API Key. Get it in the [Azure Portal](https://portal.azure.com)|
|OPENAI_TEMPERATURE|0.7| Azure OpenAI Temperature |
|OPENAI_MAX_TOKENS|-1| Azure OpenAI Max Tokens |
|VECTOR_STORE_TYPE| AzureSearch | Vector Store Type. Use AzureSearch for Azure Cognitive Search, leave it blank for Redis or Azure Cache for Redis Enterprise|
|AZURE_SEARCH_SERVICE_NAME| YOUR_AZURE_SEARCH_SERVICE_URL | Your Azure Cognitive Search service name. Get it in the [Azure Portal](https://portal.azure.com)|
|AZURE_SEARCH_ADMIN_KEY| AZURE_SEARCH_ADMIN_KEY | Your Azure Cognitive Search Admin key. Get it in the [Azure Portal](https://portal.azure.com)|
|REDIS_ADDRESS| api | URL for Redis Stack: "api" for docker compose|
|REDIS_PORT | 6379 | Port for Redis |
|REDIS_PASSWORD| redis-stack-password | OPTIONAL - Password for your Redis Stack|
|REDIS_ARGS | --requirepass redis-stack-password | OPTIONAL - Password for your Redis Stack|
|REDIS_PROTOCOL| redis:// | |
|CHUNK_SIZE | 500 | OPTIONAL: Chunk size for splitting long documents in multiple subdocs. Default value: 500 |
|CHUNK_OVERLAP |100 | OPTIONAL: Overlap between chunks for document splitting. Default: 100 |
|CONVERT_ADD_EMBEDDINGS_URL| http://batch/api/BatchStartProcessing | URL for Batch processing Function: "http://batch/api/BatchStartProcessing" for docker compose |
|AzureWebJobsStorage | AZURE_BLOB_STORAGE_CONNECTION_STRING FOR_AZURE_FUNCTION_EXECUTION | Azure Blob Storage Connection string for Azure Function - Batch Processing |



Optional parameters for additional features (e.g. document text extraction with OCR):

| App Setting | Value | Note |
| --- | --- | ------------- |
|BLOB_ACCOUNT_NAME| YOUR_AZURE_BLOB_STORAGE_ACCOUNT_NAME| OPTIONAL - Get it in the [Azure Portal](https://portal.azure.com) if you want to use the document extraction feature |
|BLOB_ACCOUNT_KEY| YOUR_AZURE_BLOB_STORAGE_ACCOUNT_KEY| OPTIONAL - Get it in the [Azure Portal](https://portal.azure.com)if you want to use document extraction feature|
|BLOB_CONTAINER_NAME| YOUR_AZURE_BLOB_STORAGE_CONTAINER_NAME| OPTIONAL - Get it in the [Azure Portal](https://portal.azure.com) if you want to use document extraction feature|
|FORM_RECOGNIZER_ENDPOINT| YOUR_AZURE_FORM_RECOGNIZER_ENDPOINT| OPTIONAL - Get it in the [Azure Portal](https://portal.azure.com) if you want to use document extraction feature|
|FORM_RECOGNIZER_KEY| YOUR_AZURE_FORM_RECOGNIZER_KEY| OPTIONAL - Get it in the [Azure Portal](https://portal.azure.com) if you want to use document extraction feature|
|PAGES_PER_EMBEDDINGS| Number of pages for embeddings creation. Keep in mind you should have less than 3K token for each embedding.| Default: A new embedding is created every 2 pages.|
|TRANSLATE_ENDPOINT| YOUR_AZURE_TRANSLATE_ENDPOINT| OPTIONAL - Get it in the [Azure Portal](https://portal.azure.com) if you want to use translation feature|
|TRANSLATE_KEY| YOUR_TRANSLATE_KEY| OPTIONAL - Get it in the [Azure Portal](https://portal.azure.com) if you want to use translation feature|
|TRANSLATE_REGION| YOUR_TRANSLATE_REGION| OPTIONAL - Get it in the [Azure Portal](https://portal.azure.com) if you want to use translation feature|
|VNET_DEPLOYMENT| false | Boolean variable to set "true" if you want to deploy the solution in a VNET. Please check your [Azure Form Recognizer](https://learn.microsoft.com/en-us/azure/applied-ai-services/form-recognizer/managed-identities-secured-access?view=form-recog-2.1.0) and [Azure Translator](https://learn.microsoft.com/en-us/azure/cognitive-services/translator/reference/v3-0-reference#virtual-network-support) endpoints as well.|

# DISCLAIMER
This presentation, demonstration, and demonstration model are for informational purposes only and (1) are not subject to SOC 1 and SOC 2 compliance audits, and (2) are not designed, intended or made available as a medical device(s) or as a substitute for professional medical advice, diagnosis, treatment or judgment. Microsoft makes no warranties, express or implied, in this presentation, demonstration, and demonstration model. Nothing in this presentation, demonstration, or demonstration model modifies any of the terms and conditions of Microsoft’s written and signed agreements. This is not an offer and applicable terms and the information provided are subject to revision and may be changed at any time by Microsoft.

This presentation, demonstration, and demonstration model do not give you or your organization any license to any patents, trademarks, copyrights, or other intellectual property covering the subject matter in this presentation, demonstration, and demonstration model.

The information contained in this presentation, demonstration and demonstration model represents the current view of Microsoft on the issues discussed as of the date of presentation and/or demonstration, for the duration of your access to the demonstration model. Because Microsoft must respond to changing market conditions, it should not be interpreted to be a commitment on the part of Microsoft, and Microsoft cannot guarantee the accuracy of any information presented after the date of presentation and/or demonstration and for the duration of your access to the demonstration model.

No Microsoft technology, nor any of its component technologies, including the demonstration model, is intended or made available as a substitute for the professional advice, opinion, or judgment of (1) a certified financial services professional, or (2) a certified medical professional. Partners or customers are responsible for ensuring the regulatory compliance of any solution they build using Microsoft technologies.
