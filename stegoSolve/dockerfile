FROM python:3.11-slim

# Install necessary packages for steganography and other tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    binwalk \
    steghide \
    ruby \
    build-essential \
    file \
    libimage-exiftool-perl \
    mediainfo \
    pngcheck \
    jpeginfo \
    foremost \
    pkg-config \
    default-libmysqlclient-dev \
    && gem install --no-document zpng iostruct \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


RUN gem install zsteg

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
    
EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
