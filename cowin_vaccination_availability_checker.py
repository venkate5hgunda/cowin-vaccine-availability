import requests
from datetime import datetime
from pytz import timezone
import json
import smtplib,ssl
from email.utils import formataddr

def print_log(span, center, date, isValid):
    center = center[:span].ljust(span,' ')
    date = date[:15].ljust(15,' ')
    isValid = isValid[:15].ljust(15,' ')
    log_message=f'{center} | {date} | {isValid}'
    print(log_message)
    global email_message_centers_table
    email_message_centers_table+=f'{log_message}\n'

localized_timezone = timezone("Asia/Kolkata")
localized_date = localized_timezone.localize(datetime.now())

cowin_api_url = "https://api.cowin.gov.in/api/v2/appointment/sessions/public/calendarByDistrict"
cowin_api_district_id="" # you can get this from browser console at cowin.gov.in. Request the details once through the page and capture the URL.
cowin_api_queries = {"district_id": cowin_api_district_id, "date": localized_date.strftime("%d-%m-%Y")}
cowin_api_request = requests.get(cowin_api_url,params=cowin_api_queries)
cowin_api_response = json.loads(cowin_api_request.text)

pad_length_calculation_centers = []
for center in cowin_api_response["centers"]:
    pad_length_calculation_centers.append(center["name"])
pad_length = len(max(pad_length_calculation_centers, key=len))

email_message_centers_table = ""

valid_sessions = []
invalid_sessions = []
print('-'[:pad_length+40].ljust(pad_length+40,'-'))
email_message_centers_table+='-'[:pad_length+40].ljust(pad_length+40,'-')+'\n'
print_log(pad_length,"CENTER","DATE","VALID/INVALID")
print('-'[:pad_length+40].ljust(pad_length+40,'-'))
email_message_centers_table+='-'[:pad_length+40].ljust(pad_length+40,'-')+'\n'
for center in cowin_api_response["centers"]:
    for session in center["sessions"]:
        if(session["min_age_limit"]<45 and session["available_capacity"]>0):
            session["center"]={"center_id":center["center_id"],"center_name":center["name"],"block_name":center["block_name"],"pincode":center["pincode"],"fee_type":center["fee_type"]}
            print_log(pad_length,center["name"],session["date"],"VALID")
            valid_sessions.append(session)
        else:
            print_log(pad_length,center["name"],session["date"],"INVALID")
            invalid_sessions.append(session)
print(f'Total Valid Centers: {len(valid_sessions)} \nTotal Invalid Centers: {len(invalid_sessions)}')

if(len(valid_sessions)>0):
    gmail_port=465 # default port for ssl
    gmail_hostname="smtp.gmail.com" # this is for gmail. change it based on which email service you use.
    gmail_sender_name="CoWin Vaccination Bot [AWS]" 
    gmail_sender_address="" # removed for privacy concern, of course.
    gmail_sender_password="" # removed for privacy concern, of course.
    gmail_receiver_address_list=[] # This is a list in my case. You can make this a dictionary, with [district-code, email-address] pairs if folks are from different areas.
    # gmail_sender_name=input(f'Enter Sender Name: ')
    # gmail_sender_address=input(f'Enter Sender e-Mail Address: ')    
    # gmail_sender_password=input(f'Enter Password for {gmail_sender_address}: ')
    # gmail_receiver_address=input(f'Enter Receiver e-Mail Address: ')
    gmail_context=ssl.create_default_context()

    email_subject=f'CoWin Vaccination NOW at {len(valid_sessions)} Centers'
    email_message=f'SUMMARY:\n{email_message_centers_table}\n\nDETAILS:\n{json.dumps(valid_sessions,sort_keys=True,indent=2)}'
    
    with smtplib.SMTP_SSL(host=gmail_hostname,port=gmail_port,context=gmail_context) as server:
        server.login(gmail_sender_address,gmail_sender_password)
        for gmail_receiver_address in gmail_receiver_address_list:
            server.sendmail(formataddr((gmail_sender_name,gmail_sender_address)),gmail_receiver_address,f'From: {gmail_sender_name} <{gmail_sender_address}> \nTo: {gmail_receiver_address} \nSubject: {email_subject}\n\n{email_message}')