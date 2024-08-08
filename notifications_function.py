import boto3
import json

ses = boto3.client('ses', region_name='us-east-1')  # Adjust region as needed

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            # Extract data from the DynamoDB record
            new_image = record['dynamodb']['NewImage']
            first_name = new_image['firstName']['S']
            last_name = new_image['lastName']['S']
            date = new_image['date']['S']
            time = new_image['time']['S']
            
            # Construct the email
            subject = 'New Attendance Record'
            body = f"{first_name} {last_name}, your attandance has been recorded on {date} at {time}. Have a great day!"
            recipient = 'revanthpavan@outlook.com'  # Replace with actual recipient email

            # Send the email
            send_email(subject, body, recipient)

def send_email(subject, body, recipient):
    response = ses.send_email(
        Source='pavanrevanth97@gmail.com',  # Replace with your SES verified email
        Destination={
            'ToAddresses': [recipient],
        },
        Message={
            'Subject': {
                'Data': subject,
            },
            'Body': {
                'Text': {
                    'Data': body,
                }
            }
        }
    )
    print("Email sent! Message ID:", response['MessageId'])
