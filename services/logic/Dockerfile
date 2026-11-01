FROM python:3.14-slim
WORKDIR /festhub

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/concerts/concerts.proto services/artists/artists.proto services/categories/categories.proto services/media/media.proto protos/
RUN python -m grpc_tools.protoc \
    -I protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/*.proto

COPY common common
COPY services/logic logic
COPY services/logic/backend-server.py .

CMD ["python", "backend-server.py"]
