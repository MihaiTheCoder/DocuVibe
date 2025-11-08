# Azure Deployment Guide

## Overview
This guide covers deploying VibeDocs to Azure for dev/test environments.

## Architecture
- **Frontend**: Azure Storage Static Website
- **Backend**: Azure App Service (Linux/Python)
- **Database**: Azure Database for PostgreSQL
- **Vector DB**: Qdrant on Azure App Service with persistent storage
- **File Storage**: Azure Blob Storage
- **CI/CD**: GitHub Actions

## Prerequisites
- Azure subscription
- Azure CLI installed
- GitHub repository with Actions enabled

## Setup Instructions

### 1. Run Infrastructure Setup
```bash
cd infrastructure
chmod +x setup-azure.sh
./setup-azure.sh
```

### 2. Configure GitHub Secrets
Add these secrets to your GitHub repository:
- `AZURE_CREDENTIALS`: Service principal JSON
- `DATABASE_URL`: PostgreSQL connection string
- `AZURE_STORAGE_CONNECTION_STRING`: Storage account connection

### 3. Deploy Applications
Push to main branch to trigger deployments:
```bash
git add .
git commit -m "Deploy to Azure"
git push origin main
```

### 4. Access Applications
- Frontend: `https://vibedocsstorage.z6.web.core.windows.net/`
- Backend API: `https://app-vibedocs-backend-dev.azurewebsites.net/api/v1/health`
- Qdrant: `https://app-vibedocs-qdrant-dev.azurewebsites.net/`

## Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `AZURE_STORAGE_CONNECTION_STRING`: Blob storage connection
- `QDRANT_HOST`: Qdrant service URL

### Frontend
- `VITE_API_URL`: Backend API URL

## Troubleshooting

### Backend not starting
- Check App Service logs: `az webapp log tail --name app-vibedocs-backend-dev`
- Verify database connection
- Check Python version compatibility

### Qdrant data persistence
- Ensure file share is mounted correctly
- Check storage account permissions

### Frontend not loading
- Verify static website is enabled on storage account
- Check CORS settings on backend
