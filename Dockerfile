FROM python:3.9-slim

# Install system dependencies if needed (e.g. for building packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Use PORT env variable (Render sets this automatically, defaults to 10000)
ENV PORT=10000
EXPOSE $PORT

# Run the app using Gunicorn — bind to $PORT so it works on both Render and Hugging Face
CMD gunicorn -b 0.0.0.0:$PORT app:app
