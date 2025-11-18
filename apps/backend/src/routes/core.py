from fastapi import Depends, APIRouter, HTTPException

from .models import QueryRequest

router = APIRouter()

@router.post("/test")
def conversation(request: QueryRequest):
    return {
        "message": f'test: {request.query}'
    }
