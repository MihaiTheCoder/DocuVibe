#!/bin/bash
# Azure resource setup script

# Variables
RESOURCE_GROUP="DocuVibes"  # Existing resource group
LOCATION="westeurope"
STORAGE_ACCOUNT="vibedocsstorage"  # Must be globally unique
APP_SERVICE_PLAN="asp-vibedocs-dev"
BACKEND_APP="app-vibedocs-backend-dev"
QDRANT_APP="app-vibedocs-qdrant-dev"
POSTGRES_SERVER="psql-vibedocs-northeu-dev"
POSTGRES_LOCATION="northeurope"  # Note: westeurope restricted for this subscription
DB_NAME="vibedocs"
DB_ADMIN="vibedocsadmin"
DB_PASSWORD="YourSecurePassword123!"  # Change this!

# Note: Resource group already exists, skipping creation
# az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account for documents
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Create container for documents
az storage container create \
  --name documents \
  --account-name $STORAGE_ACCOUNT \
  --public-access off \
  --auth-mode key

# Create App Service Plan (Linux)
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --is-linux \
  --sku B1  # Basic tier for dev/test

# Create Azure Database for PostgreSQL
# Note: Using northeurope location due to subscription restrictions in westeurope
az postgres flexible-server create \
  --name $POSTGRES_SERVER \
  --resource-group $RESOURCE_GROUP \
  --location $POSTGRES_LOCATION \
  --admin-user $DB_ADMIN \
  --admin-password $DB_PASSWORD \
  --tier Burstable \
  --sku-name Standard_B1ms \
  --version 15 \
  --storage-size 32 \
  --public-access 0.0.0.0-255.255.255.255  # Open for dev, restrict later

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $POSTGRES_SERVER \
  --database-name $DB_NAME

# Create Web App for Backend
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $BACKEND_APP \
  --runtime "PYTHON:3.11"

# Create Web App for Qdrant with persistent storage
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $QDRANT_APP \
  --deployment-container-image-name "qdrant/qdrant:latest"

# Create Azure File Share for Qdrant storage
az storage share create \
  --name qdrant-storage \
  --account-name $STORAGE_ACCOUNT \
  --quota 10

# Mount file share to Qdrant App Service
az webapp config storage-account add \
  --resource-group $RESOURCE_GROUP \
  --name $QDRANT_APP \
  --custom-id QdrantStorage \
  --storage-type AzureFiles \
  --share-name qdrant-storage \
  --account-name $STORAGE_ACCOUNT \
  --mount-path /qdrant/storage \
  --access-key $(az storage account keys list --resource-group $RESOURCE_GROUP --account-name $STORAGE_ACCOUNT --query '[0].value' -o tsv)
