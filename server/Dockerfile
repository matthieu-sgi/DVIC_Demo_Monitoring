FROM python:3.8

# Set the working directory to /app

WORKDIR /app

# Copy the current directory contents into the container at /app

COPY . /app

# Install any needed packages specified in requirements.txt

RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Launch the api using uvicorn

CMD ["uvicorn", "dvic_log_server.api:app", "--host", "0.0.0.0", "--port", "9240"]

