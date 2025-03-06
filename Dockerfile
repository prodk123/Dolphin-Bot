# Use the official Python image
FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y stockfish

# Set the working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask runs on
EXPOSE 5000

# Run the Flask app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
