# Aurora Tracker
The Aurora Tracker is designed to run within a Docker container, ensuring a consistent and isolated environment for execution. Below is the directory structure of the project:
```sh
├── aurora.py                   # The Main Script
├── build_docker_container.sh   # nothing fancy, create docker image and run docker compose
├── crontab                     # Cron job configuration file
├── docker-compose.yaml         # Docker Compose configuration
├── Dockerfile                  # Instructions for building the Docker image
├── receiver_email_list.txt     # List of email addresses for notifications
└── requirements.txt            # Python dependencies
```
#### How to Run the Aurora Tracker
1. **Set Up the Cron Job**: Edit the crontab file to specify how often you want the script to run. For example, to run the script daily at 2 AM
    ```sh
    0 2 * * * /usr/local/bin/python /app/aurora.py >> /var/log/cron.log 2>&1
    ```
2. **Add the Receivers Email**: 
    ```txt
    xyz1@gmail.com
    xyz2@gmail.com
    xyz3@gmail.com
    ```
3. **Add your Email Details**: Fill out the .env file with email details
    ```env
    EMAIL_PASSWORD='YOUR-PASSWORD'
    USERNAME='YOUR-EMAIL'
    ```
4. **Build the Docker Container**: To build the Docker container, run the following command in your terminal:
    ```sh
    ./build_docker_container.sh
    ```