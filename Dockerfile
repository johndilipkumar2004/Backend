FROM python:3.11-slim

# Install system dependencies for dlib/face-recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install dlib first separately
RUN pip install --upgrade pip
RUN pip install cmake
RUN pip install dlib==19.24.2
RUN pip install face-recognition==1.3.0
RUN pip install -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]