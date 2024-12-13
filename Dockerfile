# Download environment for container
FROM python:3
# Copy application code into container
COPY . /usr/src/app 
WORKDIR /usr/src/app
# Install dependencies
RUN pip install -r requirements.txt
# Specifies default command when container starts
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
