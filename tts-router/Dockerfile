FROM python:3.11-slim
RUN pip install --no-cache-dir fastapi==0.115.* "uvicorn[standard]==0.32.*" httpx==0.27.* numpy==2.1.*
WORKDIR /app
COPY app.py .
ENV TZ=Asia/Tokyo
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8020"]
