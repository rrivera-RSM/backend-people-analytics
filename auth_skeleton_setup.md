# Auth skeleton

## Overview

As the name implies, this skeleton is just a structure/framework that needs flesh (endpoints/features) added to it. It works as a starting point to begin development for a Python project.

This authentication skeleton sets up Single-Tenant Azure AD authentication for your FastAPI app, letting you secure your endpoints with Azure Active Directory. It's a ready-to-use foundation for FastAPI projects that need Microsoft AD authentication.

Using this skeleton cuts down setup time by handling repetitive Azure AD configuration out of the box. You get consistent authentication patterns and solid security practices without reinventing the wheel. Since all the authentication logic is centralized, it's easier to update and patch things later, so you can focus on building features instead of wrestling with auth setup.

## Prerequisites

- Azure AD tenant
- FastAPI application
- Python 3.7+
- Dependencies listed in `requirements.txt`

#### Install Required Packages

```bash
pip install -r requirements.txt
```

### Azure AD Configuration

For detailed Azure AD setup instructions, refer to the [fastapi-azure-auth documentation](https://intility.github.io/fastapi-azure-auth/single-tenant/azure_setup).

**Key configuration steps:**

1. **Register your application in Azure AD** - Navigate to Azure Portal > Azure Active Directory > App registrations and create a new application registration for your FastAPI project.
2. **Create a client secret** - Generate a client secret in the Certificates & secrets section to securely authenticate your application.
3. **Grant API permissions** - Add Microsoft Graph API permissions under API permissions to enable user and directory access as needed.
4. **Configure redirect URIs** - Set redirect URIs in Authentication settings to match your FastAPI application's callback endpoints (e.g., `http://localhost:8000/oauth2-redirect`).
5. **Collect credentials** - Gather your Tenant ID, Client ID, and Client Secret from the application overview and store them securely for use in your application configuration.
