FROM python:3.10

# Add system tools needed for the app
RUN apt-get update && apt-get install -y \
    iputils-ping traceroute dnsutils curl net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "app.py"]
