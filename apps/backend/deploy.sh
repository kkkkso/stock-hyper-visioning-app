export $(grep -v '^#' .env | xargs)
az webapp config set \
  --startup-file "gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 main:app" \
  --name $APP_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP_NAME

az webapp up \
    --name $APP_SERVICE_NAME \
    --plan $PLAN_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --os-type Linux \
    --location eastus2 \
    --runtime "Python|3.12" \
    --sku B1 \
    --logs

