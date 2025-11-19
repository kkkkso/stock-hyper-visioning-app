#!/bin/sh
# Variable block
location="East US"
resourceGroup="redis-cache-rg"
tag="create-manage-cache"
cache="redis-cache-test"
sku="Balanced_B1"

# Create a resource group
echo "Creating $resourceGroup in "$location"..."
az group create --resource-group $resourceGroup --location "$location" --tags $tag

# Create a Balanced B1 Azure Managed Redis cache
echo "Creating $cache"
az redisenterprise create --name $cache --resource-group $resourceGroup --location "$location" --sku $sku