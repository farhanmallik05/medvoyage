FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Run test suite to verify marketplace and matching integrity
RUN python -m pytest

# Expose API and marketplace UI port
EXPOSE 8000

# Default command starts the MedVoyage marketplace service
CMD ["uvicorn", "medvoyage.api:app", "--host", "0.0.0.0", "--port", "8000"]
