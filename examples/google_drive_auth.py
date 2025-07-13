"""
This script is a placeholder to guide you through Google Drive API authentication.

To use the GoogleDriveStorageProvider, you need to enable the Google Drive API
and get a `credentials.json` file for a Desktop Application.

Follow these steps:

1.  Go to the Google Cloud Console: https://console.cloud.google.com/

2.  Create a new project or select an existing one.

3.  Enable the "Google Drive API":
    - In the navigation menu, go to "APIs & Services" > "Library".
    - Search for "Google Drive API" and click "Enable".

4.  Create OAuth 2.0 Credentials:
    - Go to "APIs & Services" > "Credentials".
    - Click "+ CREATE CREDENTIALS" and select "OAuth client ID".
    - If prompted, configure the "OAuth consent screen". For an internal tool, you can select "Internal" or "External" and fill in the required fields (app name, user support email, developer contact).
    - For "Application type", select "Desktop app".
    - Give it a name (e.g., "KnowledgeBaseAgentClient").
    - Click "Create".

5.  Download your credentials:
    - A window will pop up with your client ID and secret. Click "DOWNLOAD JSON".
    - Rename the downloaded file to `credentials.json`.
    - Place this `credentials.json` file in the root directory of this project, or specify its path in the provider configuration.

6.  Run the application:
    - The first time you run the application with the Google Drive provider, a browser window will open asking you to authorize access.
    - Log in with your Google account and grant the requested permissions.
    - After you approve, a `token.json` file will be created automatically. This file stores your access and refresh tokens, so you won't have to log in every time.

IMPORTANT:
- Keep your `credentials.json` and `token.json` files secure. Do not commit them to version control.
- Add `token.json` and `credentials.json` to your `.gitignore` file.
"""

print("This is a helper script. Please read the instructions within the file to set up Google Drive authentication.")
