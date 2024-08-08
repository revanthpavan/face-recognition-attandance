import boto3
import json

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition', region_name='us-east-1')
dynamodbTableName = 'employee'
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
employeeTable = dynamodb.Table('employee')
bucketName = 'mars-employees-daily-images'

def lambda_handler(event, context):
    print(event)
    objectKey = event['queryStringParameters']['objectKey']
    image_bytes = s3.get_object(Bucket=bucketName, Key=objectKey)['Body'].read()
    response = rekognition.search_faces_by_image(
        CollectionId='employees',
        Image={'Bytes': image_bytes}
    )

        for match in response['FaceMatches']:
            print(match['Face']['FaceId'], match['Face']['Confidence'])
            face = employeeTable.get_item(
                Key={
                    'rekognitionId': match['Face']['FaceId']
                }
            )
            if 'Item' in face:
                firstName = face['Item']['firstName']
                lastName = face['Item']['lastName']
                print('Person Found: ', face['Item'])
                
                # Record attendance
                record_attendance(match['Face']['FaceId'], firstName, lastName)
                
                return build_response(200, {
                    'Message': 'Success',
                    'firstName': firstName,
                    'lastName': lastName
                })
        
        # If no matches found, send an email notification
        send_unregistered_person_email(objectKey)

        print('Person could not be recognized.')
        return build_response(403, {'Message': 'Person Not Found'})
    except Exception as e:
        print(f"Error processing image {objectKey} from bucket {bucketName}: {e}")
        return build_response(500, {'Message': 'Internal Server Error'})

def record_attendance(faceId, firstName, lastName):
    # Get the current UTC timestamp
    utc_now = datetime.utcnow()
    
    # Convert UTC to EST
    utc_timezone = pytz.utc
    est_timezone = pytz.timezone('America/New_York')
    utc_now = utc_timezone.localize(utc_now)  # Localize UTC time
    est_time = utc_now.astimezone(est_timezone)  # Convert to EST

    # Format the timestamp, date, and time
    timestamp = est_time.isoformat()  # Full timestamp in ISO format
    date = est_time.date().isoformat()  # Date in YYYY-MM-DD format
    time = est_time.strftime("%H:%M")  # Format time to HH:MM

    attendanceTable.put_item(
        Item={
            'rekognitionId': faceId,
            'timestamp': timestamp,  # Include the full timestamp as required
            'date': date,            # Store date separately
            'time': time,            # Store time in HH:MM format
            'firstName': firstName,
            'lastName': lastName
        }
    )

def send_unregistered_person_email(objectKey):
    sender = 'xxxxxxx@gmail.com'  # Replace with your SES verified sender email
    recipient = 'xxxxxx@outlook.com'  # Replace with the recipient's email
    subject = 'Unregistered Person Detected'
    body_text = f'A person in the image {objectKey} could not be recognized as registered.'

    try:
        response = ses.send_email(
            Source=sender,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        print("Email sent! Message ID:", response['MessageId'])
    except Exception as e:
        print("Error sending email:", e)
    for match in response['FaceMatches']:
        print(match['Face']['FaceId'], match['Face']['Confidence'])
        face = employeeTable.get_item(
            Key={
                'rekognitionId': match['Face']['FaceId']
            }
        )
        if 'Item' in face:
            print('Person Found: ', face['Item'])
            return build_response(200, {
            'Message': 'Success',
            'firstName': face['Item']['firstName'],
            'lastName': face['Item']['lastName']
            })
    print('Person could not be recognized.')
    return build_response(403, {'Message': 'Person Not Found'})

def build_response(status_code, body=None):
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }
    if body is not None:  
        response['body'] = json.dumps(body)  
    return response
