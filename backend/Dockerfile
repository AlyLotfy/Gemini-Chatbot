# 1. Use an official Python runtime as a parent image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your backend code (main.py, etc.) into the container
COPY . .

# 6. Expose the port your app runs on
EXPOSE 8000

# 7. Define the command to run your app
# We use --host 0.0.0.0 to make it accessible outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]