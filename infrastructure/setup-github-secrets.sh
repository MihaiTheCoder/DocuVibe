#!/bin/bash
# Create service principal for GitHub Actions

SUBSCRIPTION_ID="9c1ca7e4-523d-4698-ba0f-df17d4322b8c"
RESOURCE_GROUP="DocuVibes"

echo "Creating service principal for GitHub Actions..."
echo "================================================"

# Create service principal
az ad sp create-for-rbac \
  --name "github-actions-vibedocs" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth

echo ""
echo "Copy the JSON output above and add it as AZURE_CREDENTIALS secret in GitHub"
echo "GitHub repo: https://github.com/MihaiTheCoder/DocuVibe/settings/secrets/actions"
echo ""
echo "================================================"
echo "Getting storage connection string..."
echo "================================================"

# Get storage connection string
az storage account show-connection-string \
  --name vibedocsstorage \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv

echo ""
echo "Copy the connection string above and add it as AZURE_STORAGE_CONNECTION_STRING secret in GitHub"
echo ""
echo "================================================"
echo "Database URL (update with your password):"
echo "================================================"

# Construct DATABASE_URL
echo "postgresql://vibedocsadmin:YourSecurePassword123!@psql-vibedocs-dev.postgres.database.azure.com/vibedocs?sslmode=require"
echo ""
echo "Copy the DATABASE_URL above and add it as DATABASE_URL secret in GitHub"
