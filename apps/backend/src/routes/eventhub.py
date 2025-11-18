from fastapi import APIRouter

router = APIRouter()


@router.post("/output")
async def send_eventhub_message(payload: dict):
    #
    # Example Event Message function...
    #
    return {"status": "test", "result": f"test received: {payload}"}

