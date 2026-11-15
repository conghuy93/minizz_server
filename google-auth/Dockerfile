FROM python:3.11-slim
RUN pip install --no-cache-dir fastapi==0.115.* "uvicorn[standard]==0.32.*" httpx==0.27.* pymysql==1.1.* bcrypt==4.2.*
WORKDIR /app
COPY app.py .
ENV TZ=Asia/Tokyo
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090", "--proxy-headers", "--forwarded-allow-ips", "*"]
