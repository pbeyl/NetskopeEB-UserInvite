import logging
import os
import requests
import azure.functions as func

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Create a FunctionApp instance for V2 programming model ---
# This is crucial for Azure Functions to discover and run your functions.
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# --- Configuration (to be set as Application Settings in Azure Portal) ---
# The tenant name or ID for the GoSkope API URL (e.g., "yourcompany")
GOSKOPE_TENANT_NAME = os.environ.get('GOSKOPE_TENANT_NAME')
# The bearer token for authenticating with the GoSkope API
GOSKOPE_API_TOKEN = os.environ.get('GOSKOPE_API_TOKEN')
# Use these variables to customise the text displayed to the user
CUSTOM_SUCCESS_TEXT = os.environ.get('CUSTOM_SUCCESS_TEXT')
CUSTOM_FAILURE_TEXT = os.environ.get('CUSTOM_FAILURE_TEXT')

# Ensure essential environment variables are set
if not GOSKOPE_TENANT_NAME:
    logger.error("GOSKOPE_TENANT_NAME environment variable is not set.")
if not GOSKOPE_API_TOKEN:
    logger.error("GOSKOPE_API_TOKEN environment variable is not set.")

# Set default message text if the custom text variables are not set
if not CUSTOM_SUCCESS_TEXT:
    CUSTOM_SUCCESS_TEXT = f"""Please open <span class="font-semibold text-blue-600"><a href="https://outlook.office.com/" target="_blank">Outlook</a></span> and follow the steps in the email to install and enrol the Enterprise Browser."""
if not CUSTOM_FAILURE_TEXT:
    CUSTOM_FAILURE_TEXT = f"Your user may not be provisioned. Please contact the security team to assist with installing the Enterprise Browser."

# --- Azure Function HTTP Trigger ---
# Decorate the 'main' function to register it as an HTTP trigger.
# 'route' defines the URL path (e.g., /api/GoSkopeInviteTrigger).
# 'methods' specifies the HTTP methods it responds to (e.g., GET, POST).
@app.route(route="trigger_userinvite", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "POST"])
def trigger_userinvite(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('Python HTTP trigger function processed a request.')

    # 1. Entra ID Authentication (via App Service Authentication)
    # When App Service Authentication is enabled, user claims are passed in headers.
    # X-MS-CLIENT-PRINCIPAL-ID contains the object ID of the authenticated user.
    # X-MS-CLIENT-PRINCIPAL-NAME contains the UPN/email.
    auth_user_id = req.headers.get('X-MS-CLIENT-PRINCIPAL-ID')
    auth_user_name = req.headers.get('X-MS-CLIENT-PRINCIPAL-NAME')

    if not auth_user_name:
        logger.warning("Unauthorized: X-MS-CLIENT-PRINCIPAL-ID header not found. "
                       "Ensure App Service Authentication is configured.")
        return func.HttpResponse(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Unauthorized</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body {{ font-family: 'Inter', sans-serif; }}
                </style>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
                <div class="bg-white p-8 rounded-lg shadow-md text-center">
                    <h1 class="text-2xl font-bold text-red-600 mb-4">Authentication Required</h1>
                    <p class="text-gray-700">Please ensure you are authenticated via Entra ID to access this service.</p>
                    <p class="text-sm text-gray-500 mt-2">Error: X-MS-CLIENT-PRINCIPAL-NAME header not found.</p>
                </div>
            </body>
            </html>
            """,
            status_code=401,
            mimetype="text/html"
        )
    
    logger.info(f"Authenticated User ID: {auth_user_id}, Name: {auth_user_name}")

    # Check if configuration variables are set
    if not GOSKOPE_TENANT_NAME or not GOSKOPE_API_TOKEN:
        logger.error("Missing required configuration variables.")
        return func.HttpResponse(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Configuration Error</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body {{ font-family: 'Inter', sans-serif; }}
                </style>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
                <div class="bg-white p-8 rounded-lg shadow-md text-center">
                    <h1 class="text-2xl font-bold text-red-600 mb-4">Internal Server Error</h1>
                    <p class="text-gray-700">Function not properly configured. Please check application environment variables.</p>
                </div>
            </body>
            </html>
            """,
            status_code=500,
            mimetype="text/html"
        )

    # Rate Limiting Logic has been removed as per request.
    # The function will now proceed directly to the API call if authenticated and configured.

    # 2. Prepare and Send POST Request to GoSkope API
    api_url = f'https://{GOSKOPE_TENANT_NAME}.goskope.com/api/v2/nsbrowser/invite'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GOSKOPE_API_TOKEN}'
    }
    data = {
        "invitation": {
            "userIds": [auth_user_name],
            "userGroupIds": [],
            "organizationalUnits": []
        },
        "sendInvitationEmail": True,
        "emailTemplate": 0
    }

    try:
        logger.info(f"Sending POST request to {api_url} for user {auth_user_name}...")
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        logger.info(f"GoSkope API response status: {response.status_code}")
        logger.info(f"GoSkope API response body: {response.text}")

        # Success Page
        return func.HttpResponse(
            f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Onboarding Email Successfully Sent</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body {{ font-family: 'Inter', sans-serif; }}
                </style>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
                <div class="bg-white p-8 rounded-lg shadow-md text-center">
                    <h1 class="text-2xl font-bold text-green-600 mb-4">Onboarding Email Successfully Sent!</h1>
                    <p class="text-gray-700">Onboarding email has been successfully sent to <span class="font-semibold text-blue-600">{auth_user_name}</span>.</p>
                    <p class="text-gray-700 mt-2">{CUSTOM_SUCCESS_TEXT}</p>
                </div>
            </body>
            </html>
            """,
            status_code=200,
            mimetype="text/html"
        )

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err} - Response: {http_err.response.text}")
        # Error Page for HTTP errors
        return func.HttpResponse(
            f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Onboarding Failed</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body {{ font-family: 'Inter', sans-serif; }}
                </style>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
                <div class="bg-white p-8 rounded-lg shadow-md text-center">
                    <h1 class="text-2xl font-bold text-red-600 mb-4">Onboarding Failed</h1>
                    <p class="text-gray-700">{CUSTOM_FAILURE_TEXT}</p>
                    <p class="text-sm text-gray-500 mt-2">Error: API responded with status {http_err.response.status_code}. User: {auth_user_name}</p>
                </div>
            </body>
            </html>
            """,
            status_code=http_err.response.status_code,
            mimetype="text/html"
        )
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred: {conn_err}")
        # Error Page for connection errors
        return func.HttpResponse(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Onboarding Failed</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body {{ font-family: 'Inter', sans-serif; }}
                </style>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
                <div class="bg-white p-8 rounded-lg shadow-md text-center">
                    <h1 class="text-2xl font-bold text-red-600 mb-4">Onboarding Failed</h1>
                    <p class="text-gray-700">{CUSTOM_FAILURE_TEXT}</p>
                    <p class="text-sm text-gray-500 mt-2">Error: Could not connect to the GoSkope API.</p>
                </div>
            </body>
            </html>
            """,
            status_code=503, # Service Unavailable
            mimetype="text/html"
        )
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred: {timeout_err}")
        # Error Page for timeout errors
        return func.HttpResponse(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Onboarding Failed</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body {{ font-family: 'Inter', sans-serif; }}
                </style>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
                <div class="bg-white p-8 rounded-lg shadow-md text-center">
                    <h1 class="text-2xl font-bold text-red-600 mb-4">Onboarding Failed</h1>
                    <p class="text-gray-700">{CUSTOM_FAILURE_TEXT}</p>
                    <p class="text-sm text-gray-500 mt-2">Error: GoSkope API did not respond in time.</p>
                </div>
            </body>
            </html>
            """,
            status_code=504, # Gateway Timeout
            mimetype="text/html"
        )
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An unexpected error occurred during API call: {req_err}")
        # Generic Error Page for other request exceptions
        return func.HttpResponse(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Onboarding Failed</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body {{ font-family: 'Inter', sans-serif; }}
                </style>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
                <div class="bg-white p-8 rounded-lg shadow-md text-center">
                    <h1 class="text-2xl font-bold text-red-600 mb-4">Onboarding Failed</h1>
                    <p class="text-gray-700">{CUSTOM_FAILURE_TEXT}</p>
                    <p class="text-sm text-gray-500 mt-2">An unexpected error occurred during the API call.</p>
                </div>
            </body>
            </html>
            """,
            status_code=500,
            mimetype="text/html"
        )
    except Exception as e:
        logger.error(f"An unhandled error occurred: {e}")
        # Generic Error Page for any unhandled exceptions
        return func.HttpResponse(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Onboarding Failed</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body {{ font-family: 'Inter', sans-serif; }}
                </style>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
                <div class="bg-white p-8 rounded-lg shadow-md text-center">
                    <h1 class="text-2xl font-bold text-red-600 mb-4">Onboarding Failed</h1>
                    <p class="text-gray-700">{CUSTOM_FAILURE_TEXT}</p>
                    <p class="text-sm text-gray-500 mt-2">An unhandled internal server error occurred.</p>
                </div>
            </body>
            </html>
            """,
            status_code=500,
            mimetype="text/html"
        )
