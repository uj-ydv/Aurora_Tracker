# Use the official Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file into the container
COPY . .

# Install the dependencies
RUN pip install -r requirements.txt

# Install cron
RUN apt-get update && apt-get install -y cron

# Copy the crontab file into the cron.d directory
COPY crontab /etc/cron.d/my-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/my-cron

# Apply the cron job
RUN crontab /etc/cron.d/my-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
# Run the command on container startup using JSON array format
# CMD ["cron", "-f"]
# CMD cron && tail -f /var/log/cron.log
# Run the command on container startup using JSON array format
CMD ["sh", "-c", "cron -f && tail -f /var/log/cron.log"]