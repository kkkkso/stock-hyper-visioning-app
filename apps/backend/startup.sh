python -m uvicorn main:app --host 0.0.0.0 --port 8000
# gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 main:app