# Azure Managed Redis

엔터프라이즈 급 Redis 인스턴스를 생성합니다.
자세한 내용은 [링크](https://learn.microsoft.com/ko-kr/azure/redis/scripts/create-manage-cache?pivots=azure-managed-redis)를 참조하세요.

## 빠른 시작

```sh
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
```

레디스 인스턴스가 생성되었다면, 각종 인증 정보를 코드 내에 Deploy하여야 합니다.

**특히, 백엔드 단에서 Authentication 관련하여서는 Microsoft Entra ID를 사용하는 경우 별도 설정을 거쳐야 합니다.**

[Python 예제 코드](https://learn.microsoft.com/ko-kr/azure/redis/python-get-started)
