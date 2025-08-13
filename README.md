# Netskope Enterprise Browser Self Enrolment Workflow

The Netskope Enterprise Browser is often used to provide secure 
application access through a corporate controlled browser when user 
access these applications from unmanaged BYOD devices. The current 
email based onboarding flow requires a Netskope Administrator to 
manually send an invitation to the end user.

This guide offers a way to create an Azure Function App (Serverless
Function) that will leverage the Netskope Browser invite API to enable
users to self onboard. This is a proof of concept but should inspire
customers with what can be possible through API automation.

The steps below might seem intimidating however the configuration is
quite straight forward and easy to get done.

### Pre-requisites

The following pre-requisites are required to leverage this solution.

- Netskope Enterprise Browser Subscription

- Microsoft Entra ID as idP

- Microsoft Azure with ability to create Function App

- Rest APIv2 Token for Endpoint /api/v2/nsbrowser/invite

### Instructions

These instruction will cover the following main aspects of deploying the
solution

1.  Netskope Tenant Configuration

2.  Azure Portal Setup

3.  Configure the Azure App

4.  FunctionApp Code Deployment

### 1. Netskope Tenant Configuration

- Login to the target Netskope Tenant

- Navigate to Settings → Tools → Rest API v2

- Create a New Token with Access to **/api/v2/nsbrowser/invite**

Keep a copy the **Token** (we will need this when configuring the Azure
Function App environment variables)

### 2. Azure Portal Setup

### **Create an Azure Function App:**

- Go to the [Azure Portal](https://portal.azure.com/).

- Setup the Required Pre-requisites

  - **Subscription:** Select your Azure subscription.

  - **Resource Group:** Create a new one (e.g., NetskopeDemo) or choose
    an existing one.

  - **Storage account:** Create a new storage account (e.g.,
    NetskopeUserInviteAppStorage) or select an existing one. This
    storage account is essential for the Function App\'s operation.

- In the search bar at the top, type \"Function App\" and select
  \"Function App\" from the results.

- Click \"+ Create\".

- Fill in the required details:

  - **Hosting plan:** For most serverless scenarios, Consumption
    (Serverless) is appropriate.

  - **Function App name:** Choose a globally unique name (e.g.,
    NetskopeUserInviteApp).

  - **Publish:** Select Code.

  - **Runtime stack:** Select Python.

  - **Version:** Choose 3.12.

  - **Region:** Select a region close to your users or resources.

  - **Operating System:** Select Linux.

  - **Application Insights:** You can enable this for monitoring, but
    it\'s optional for initial setup.

- Click \"Review + create\", then \"Create\". Wait for the deployment to
  complete.

**Configure App Service Authentication (Entra ID / Easy Auth):**

- Once your Function App is deployed, navigate to its resource in the
  Azure Portal.

- In the left-hand navigation pane, under **Settings**, click on
  **Authentication**.

- Click \"Add identity provider\".

- **Identity provider:** Select Microsoft.

- **App registration:**

  - Select Create new registration.

  - **App registration name:** Provide a descriptive name (e.g., Onboard
    Netskope Enterprise Browser ).

  - **Supported account types:** Keep the default or choose as per your
    organization\'s Entra ID setup.

- **App Service authentication settings:** Select Require
  authentication. For unauthenticated requests select HTTP 302 Found
  redirect: recommended for websites

- Click \"**Add**\".

- This step secures your function endpoint, ensuring only users
  authenticated by Entra ID can access it. The authenticated user\'s ID
  will then be passed in the X-MS-CLIENT-PRINCIPAL-NAME header, which
  the Python code uses.

### 3. Configure the Azure App (Environment Variables)

- In your Function App, in the left-hand navigation pane, under
  **Settings**, click on **Environment Variables**.

- Go to the **App settings** tab.

- Click \"+ New application setting\" for each of the following and
  provide their values:

  - **Name:** GOSKOPE_TENANT_NAME

    - **Value:** Your Netskope tenant name (e.g., if your Netskope
      Tenant URL is https://mycompany.eu.goskope.com/\..., then the
      value here would be mycompany.eu).

  - **Name:** GOSKOPE_API_TOKEN

    - **Value:** Your bearer token for authenticating with the Netskope
      API obtained in the first step. **This token grants access to your
      Netskope invitation endpoint.**

  - **Name:** AzureWebJobsStorage

    - **Value:** The connection string for the Azure Storage Account.

      - To get this: Go to your **Storage Account** resource (the one
        created with your Function App).

      - In the left-hand navigation, under **Security + networking**,
        click **Access keys**.

      - Copy the Connection string for key1 (or key2). It will look
        something like
        DefaultEndpointsProtocol=https;AccountName=yourstorageaccountname;AccountKey=yourlongkey;EndpointSuffix=core.windows.net.

  - **Name:** CUSTOM_SUCCESS_TEXT **(OPTIONAL)**

    - **Value:** This allows changing the default **success** text with
      custom message.

      - **Sample Value:** Please open \<a
        href=\\\"https://outlook.office.com/\\\"
        target=\\\"\_blank\\\"\>Outlook\</a\> follow the steps in the
        email to install and enrol the Enterprise Browser.

  - **Name:** CUSTOM_FAILURE_TEXT **(OPTIONAL)**

    - **Value:** This allows changing the default **failure** text with
      custom message.

      - **Sample Value:** Please contact the security team to assist
        with installing the Enterprise Browser.

- Click \"**Save**\" at the top of the Configuration blade after adding
  all settings.

### **4. FunctionApp Code Deployment**

The purpose of this section is to deploy the function app python code.

**Deploy the FunctionApp code:**

- Download the [function app from Github.](https://github.com/pbeyl/NetskopeEB-UserInvite/archive/refs/tags/v1.0.0.zip)

- Open the **Azure Cloud Shell** from the icon in the top right hand
  corner.

- Once the shell launches, select **Manage Files \> Upload** and upload
  the **functionapp.zip** file downloaded from github.

- Next use the following command to **deploy the function app code**.
  Ensure you use the resource-group and name values that match your
  configuration.

    ``` 
    az functionapp deployment source config-zip \
        --resource-group NetskopeDemo \
        --name NetskopeUserInviteApp \
        --src functionapp.zip
    ```

Running this command may take a minute or two to complete.

- Once the Deployment has completed, Click "**Overview**"

- Click on the **trigger_userinvite** to open and view the function.

- Once the page opens click the **Get function URL** and copy the
  **default (Host key) value.**

- Open the **URL "default (Host key)"** in a new browser window. This
  will redirect the user to authenticate against Entra ID and will
  execute the function app when successful.

- **User Access:** You can share this URL directly with a user to test
  authentication and to trigger the Enterprise Browser invitation
  workflow. This URL can also be used to create a new Enterprise App for
  the Microsoft myapps portal.

## Troubleshooting

Console log messages are useful for troubleshooting issues. You can view
the Function App console output through Azure.

- From the Function App configuration page

- Open the **Monitoring** Section and select **Log Stream**

