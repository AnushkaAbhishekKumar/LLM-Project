FROM python:3.12-slim-bookworm

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Use an official Python image as a base
FROM python:3.11

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    git \
    curl \
    wget \
    sqlite3 \
    ffmpeg \
    imagemagick \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*  # Clean up APT cache to reduce image size


RUN apt update && apt install -y nodejs npm
# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install \
    fastapi \
    uvicorn[standard] \
    requests \
    httpx \
    websockets

# Install data processing libraries
RUN pip install \
    pandas \
    duckdb \
    polars \
    scipy \
    numpy

# Install database-related packages
RUN pip install \
    sqlalchemy \
    psycopg2

# Install text processing packages
RUN pip install \
    beautifulsoup4 \
    black \
    pymupdf

# Install GitPython for Git interactions
RUN pip install gitpython

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ARG AIPROXY_TOKEN
ENV AIPROXY_TOKEN=$AIPROXY_TOKEN

# Expose the FastAPI port
EXPOSE 8000

# Command to run FastAPI app
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

RUN mkdir -p /data
WORKDIR /app

COPY ex.py /app

CMD [ "uv", "run", "ex.py"]

