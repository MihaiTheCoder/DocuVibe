# Development Utility Scripts

This directory contains utility scripts for database management, testing, and Azure deployment.

## Scripts Overview

### Database & User Management

- **`add_user_to_org.py`** - Add a user to an organization
- **`get_user_org.py`** - Get user's organization info using ORM
- **`get_user_org_simple.py`** - Get user's organization info using raw SQL

### Authentication & Tokens

- **`create_test_token.py`** - Generate JWT token for local testing
- **`generate_test_token.py`** - Alternative JWT token generator for testing
- **`generate_production_token.py`** - Generate production JWT token for Azure API

### Azure Database Management

- **`setup_azure_test_user.py`** - Setup test user and organization on Azure database
- **`fix_enums_azure.py`** - Fix PostgreSQL enum types on Azure database

### Testing & Debugging

- **`check_enums.py`** - Check enum values in database
- **`test_enum.py`** - Test enum value behavior

## Environment Variables

All scripts use environment variables for credentials. They support both local development and Azure App Service configuration.

### Local Development

Set environment variables in your `.env` file or shell:

```bash
# Database connection
export DATABASE_URL="postgresql://user:password@localhost:5432/vibedocs"

# For Azure-specific scripts (optional, falls back to DATABASE_URL)
export AZURE_DATABASE_URL="postgresql://user:password@azure-host/vibedocs"

# JWT Secret Key
export SECRET_KEY="your-local-secret-key"

# For production token generation (optional, falls back to SECRET_KEY)
export AZURE_SECRET_KEY="your-azure-secret-key"
```

### Azure App Service Configuration

These scripts automatically work with Azure App Service because configuration settings are exposed as environment variables.

#### View Current Configuration

```bash
az webapp config appsettings list \
  --name app-vibedocs-backend-dev \
  --resource-group DocuVibes \
  --output table
```

#### Set Configuration Values

```bash
# Set DATABASE_URL (already configured in Azure)
az webapp config appsettings set \
  --name app-vibedocs-backend-dev \
  --resource-group DocuVibes \
  --settings DATABASE_URL="postgresql://user:password@host/db"

# Set SECRET_KEY (already configured in Azure)
az webapp config appsettings set \
  --name app-vibedocs-backend-dev \
  --resource-group DocuVibes \
  --settings SECRET_KEY="your-secret-key"
```

#### Accessing Azure Configuration from WSL2

If you're running scripts from WSL2 and need to access Azure database:

```bash
# Get DATABASE_URL from Azure App Service
export DATABASE_URL=$(az webapp config appsettings list \
  --name app-vibedocs-backend-dev \
  --resource-group DocuVibes \
  --query "[?name=='DATABASE_URL'].value" \
  --output tsv)

# Get SECRET_KEY from Azure App Service
export SECRET_KEY=$(az webapp config appsettings list \
  --name app-vibedocs-backend-dev \
  --resource-group DocuVibes \
  --query "[?name=='SECRET_KEY'].value" \
  --output tsv)
```

## Usage Examples

### Local Development

```bash
# Activate virtual environment
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Check database enums
python check_enums.py

# Get user organization
python get_user_org_simple.py

# Generate test token
python generate_test_token.py
```

### Azure Database Operations

```bash
# Setup test user on Azure (using DATABASE_URL from Azure config)
export AZURE_DATABASE_URL="postgresql://..."
python setup_azure_test_user.py

# Fix enum types on Azure database
python fix_enums_azure.py

# Generate production token for Azure API
export AZURE_SECRET_KEY="..."
python generate_production_token.py
```

## Security Notes

1. **Never commit credentials** - All secrets should be in environment variables or `.env` files
2. **Use Azure Key Vault for production** - Consider migrating to Azure Key Vault for enhanced security
3. **Rotate secrets regularly** - Change production secrets periodically
4. **Restrict access** - Use Azure RBAC to control who can view/modify secrets

## Azure Key Vault Integration (Future Enhancement)

For production environments, consider using Azure Key Vault:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://your-vault.vault.azure.net/", credential=credential)

# Retrieve secrets
database_url = client.get_secret("DATABASE-URL").value
secret_key = client.get_secret("SECRET-KEY").value
```

## Troubleshooting

### "ERROR: AZURE_DATABASE_URL or DATABASE_URL environment variable not set"

**Solution:** Set the environment variable:
```bash
export DATABASE_URL="postgresql://user:password@host/db"
```

### "ERROR: AZURE_SECRET_KEY or SECRET_KEY environment variable not set"

**Solution:** Set the environment variable:
```bash
export SECRET_KEY="your-secret-key"
```

### Database connection timeout on Azure

**Solution:** Check firewall rules:
```bash
az postgres flexible-server firewall-rule list \
  --resource-group DocuVibes \
  --name psql-vibedocs-northeu-dev
```

Add your IP if needed:
```bash
az postgres flexible-server firewall-rule create \
  --resource-group DocuVibes \
  --name psql-vibedocs-northeu-dev \
  --rule-name AllowMyIP \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```
