import os
import re
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date as dt, timedelta, datetime
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Function to read data from raw.txt file and convert it into a dictionary
def get_data():
    # # Fetch data from raw.txt file --> This is for testing purposes
    # data = []
    # with open(os.path.join(os.path.dirname(__file__), 'raw.txt'), 'r') as f:
    #     for line in f:
    #         data.append(line.strip())
    
    # raw_data_string = "\n".join(data)
    # kp_lines = re.findall(r"^.*[0-9]{2}-[0-9]{2}UT.*$", raw_data_string, re.MULTILINE)
    
    ## Fetch data from the NOAA website
    raw_data = requests.get('https://services.swpc.noaa.gov/text/3-day-forecast.txt').content.decode('utf-8')
    kp_lines = re.findall("^.*[0-9]{2}-[0-9]{2}UT.*$", raw_data, re.MULTILINE)
    
    # Prepare the data dictionary
    data_dicts = []
    for entry in kp_lines:
        # Remove any 'G#' values. Don't really need {1,2} as there are only 5 levels.
        entry = re.sub(r'\(G[0-9]{1,2}\)', '    ', entry)  
        parts = entry.split()
        data_dicts.append({
            'time': parts[0],
            'date1': float(parts[1]),
            'date2': float(parts[2]),
            'date3': float(parts[3])
        })
    return data_dicts


def fetch_receiver_emails(filename):
    # Get the directory of the currently running script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Create the full path to the file
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r') as file:
            # Read lines and strip any whitespace
            emails = [line.strip() for line in file.readlines()]
        return emails
    except FileNotFoundError:
        print(f"Error: The file {filename} does not exist at {file_path}")
        return []


def send_email_notification(output):
    # Email credentials
    smtp_server = 'smtp.gmail.com'  # For Gmail
    smtp_port = 587  # For TLS
    username = os.getenv('USERNAME')
    password = os.getenv('EMAIL_PASSWORD') # Use App Password if 2FA is enabled
    
    # Set up the email parameters
    sender_email = os.getenv('USERNAME')
    receiver_email = fetch_receiver_emails('receiver_email_list.txt')  # Fetch from the text file
    subject = 'Aurora Forecast Update'
    body = f'    Forecasts indicate a possibility of seeing the aurora in the next 3 days.\n\n\
    Aurora Forecast : {output}\n\n\
    Enjoy the night, and do not forget to share your experiences if you get a chance to see the aurora!'
    
    # Create a multipart email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ', '.join(receiver_email)
    msg['Subject'] = subject
    
    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))
    
    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade to a secure connection
            server.login(username, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


def expand_kp_data(raw_data, start_date):
    expanded = []
    for i, day_label in enumerate(['date1', 'date2', 'date3']):
        for entry in raw_data:
            start_hour, end_hour = map(int, entry['time'].replace('UT', '').split('-'))
            date = start_date + timedelta(days=i)
            start_dt = datetime(date.year, date.month, date.day, start_hour)
            # Handle 00-03 or 21-00 wrapping
            end_dt = start_dt + timedelta(hours=(end_hour - start_hour) % 24)
            start_time = start_dt + timedelta(hours=10)
            end_time = end_dt + timedelta(hours=10)
            expanded.append({
                'Time': start_time.strftime("%Y-%m-%d %H:%M"),
                'End_Time': end_time.strftime("%Y-%m-%d %H:%M"),
                'kp_index': entry[day_label],
                'Date': date.strftime("%Y-%m-%d"),
            })
    return expanded

def check_aurora(expanded_data):
    # expanded_data is expected to be a list of dictionaries with 'Time', 'kp_index', and 'Date' keys
    # Sample expanded_data format: {'Time': '2025-06-01 10:00', 'End_Time':'2025-06-01 13:00', 'kp_index': 4.0, 'Date': '2025-06-01'}
    # aurora_occurence is flag to check if aurora is expected. This is true when kp_index >= 6.5.
    aurora_occurence = False
    aurora_times = []
    output_String = ""
    for entry in expanded_data:
        # check if night time
        hour = (datetime.strptime(entry['Time'], "%Y-%m-%d %H:%M")).hour
        is_night = hour >= 16 or hour < 6
        # print(f"Checking time: {entry['Time']} Hour: {hour} -- {is_night}")
        if entry['kp_index'] >= 6.5 and is_night:
            aurora_occurence = True
            aurora_times.append(entry)
            output_String += f"\nBetween {entry['Time']} and {entry['End_Time']} AEST, Aurora is expected with Kp_index {entry['kp_index']}" 
    if aurora_occurence:
        # Send email notification
        send_email_notification(output_String)
        return output_String,aurora_occurence
    else:
        output_String = "\nNo Aurora expected in the next 3 days!"
        return output_String,aurora_occurence
    

# Main function
if __name__ == '__main__':
    print(f"---------------------------- Aurora Forecast ----------------------------")
    melbourne_offset = timedelta(hours=11)  # Adjust to UTC+11 for daylight saving time
    print(f"Time now:: {(datetime.now() + melbourne_offset).strftime('%d/%m %H:%M')}")
    print(f"Running the Aurora Forecast Code...")
    raw_data = get_data()

    #### 
    start_date = datetime.today().date()  # e.g., today
    expanded_data = expand_kp_data(raw_data, start_date)
    aurora_outcome = check_aurora(expanded_data)
    print(aurora_outcome[0])

    print(f"\nCode Run Complete!")
    print(f"---------------------------- End of Code --------------------------------\n")