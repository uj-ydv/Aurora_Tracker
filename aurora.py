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

# Function to convert UTC time to AEDT time
def convert_utc_range_to_aedt(utc_time_str):
    time_range, date_str = utc_time_str.split()
    start_hour, end_hour = time_range.split('-')
    # Remove 'UT' and prepare for parsing
    start_hour = start_hour.strip('UT')
    end_hour = end_hour.strip('UT')
    
    # Parse the start and end times (adding ':00' for the minute part)
    start_utc = datetime.strptime(f"{date_str} {start_hour}:00", "%d/%m %H:%M")
    end_utc = datetime.strptime(f"{date_str} {end_hour}:00", "%d/%m %H:%M")
    
    # If the end hour is "00", it should move to the next day
    if end_hour == '00':
        end_utc += timedelta(days=1)
    
    # Convert UTC to AEDT (add 11 hours)
    start_aedt = start_utc + timedelta(hours=11)
    end_aedt = end_utc + timedelta(hours=11)
    return (
        start_aedt.strftime("%d/%m %H:%M AEDT"),
        end_aedt.strftime("%d/%m %H:%M AEDT")
    )


# Function to read data from raw.txt file and convert it into a dictionary
def get_data():
    # # Fetch data from raw.txt file --> This is for testing purposes
    # data = []
    # with open(os.path.join(os.path.dirname(__file__), 'raw.txt'), 'r') as f:
    #     for line in f:
    #         data.append(line.strip())
    
    # raw_data_string = "\n".join(data)
    # kp_lines = re.findall(r"^.*[0-9]{2}-[0-9]{2}UT.*$", raw_data_string, re.MULTILINE)

    ### Fetch data from the NOAA website
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


# Function to check for aurora based on Kp index values
def check_for_aurora(raw_data):
    flag = 0
    time = ""
    kp_date_str = ""
    kp_value = None
    # Check for Kp index values greater than or equal to 7
    for entry in raw_data:
        for key in ['date1', 'date2', 'date3']:
            if entry[key] >= 5:
                flag = 1
                time = entry['time']
                date_key = key
                kp_value = entry[key]
                break
    # Prepare the output message
    if flag == 0:
        output = f"No Aurora expected in the next 3 days!"
    else:
        if date_key == 'date1':
            kp_date_str = dt.today().strftime("%d/%m")
        elif date_key == 'date2':
            kp_date_str = (dt.today() + timedelta(days=1)).strftime("%d/%m")
        elif date_key == 'date3':
            kp_date_str = (dt.today() + timedelta(days=2)).strftime("%d/%m")
        # Convert the UTC time to AEDT time
        original_time = f"{time} {kp_date_str}"
        converted_time = convert_utc_range_to_aedt(original_time)
        output = f"Aurora expected with Kp_index {kp_value} between {converted_time[0]} and {converted_time[1]}"
        # Send email notification
        send_email_notification(output)
    return output,flag

def fetch_receiver_emails(filename):
    with open(filename, 'r') as file:
        # Read lines and strip any whitespace
        emails = [line.strip() for line in file.readlines()]
    return emails

def send_email_notification(output):
    # Email credentials
    smtp_server = 'smtp.gmail.com'  # For Gmail
    smtp_port = 587  # For TLS
    username = os.getenv('USERNAME')
    password = os.getenv('EMAIL_PASSWORD') # Use App Password if 2FA is enabled
    
    # Set up the email parameters
    sender_email = os.getenv('USERNAME')
    # receiver_email = ['ujjwal.notification@gmail.com']#, 'ydv.ujjwal088@gmail.com']
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

# Main function
if __name__ == '__main__':
    print(f"---------------------------- Aurora Forecast ----------------------------")
    melbourne_offset = timedelta(hours=11)  # Adjust to UTC+11 for daylight saving time
    print(f"Time now:: {(datetime.now() + melbourne_offset).strftime('%d/%m %H:%M')}")
    print(f"Running the Aurora Forecast Code...")
    raw_data = get_data()
    output = check_for_aurora(raw_data)
    print(output[0])
    print(f"Code Run Complete!")
    print(f"---------------------------- End of Code --------------------------------\n")
