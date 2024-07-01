FROM python:3.12-alpine

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --upgrade pip

# Copy entrypoint.sh into the image
COPY ./entrypoint.sh /app/entrypoint.sh

# Change line endings of entrypoint.sh (if necessary)
RUN sed -i 's/\r$//g' /app/entrypoint.sh

# Make entrypoint.sh executable
RUN chmod +x /app/entrypoint.sh

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
