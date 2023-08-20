def upload(s3_client,cognito_client,sub_id,username,bucket_name,file,userpool_id):
    sub_ids = get_all_sub_ids(cognito_client,userpool_id)
    region = "ap-south-1"
    filename = 'grantletter.pdf'
    for id in sub_ids:
        if id == sub_id: #sub_id is selected id from frontend
            file_key = f'{id}/{filename}'
            try:
                s3_client.upload_file(file, bucket_name, file_key)
                object_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/{file_key}'
                attribute_name = 'website'
                cognito_data_uploader(cognito_client, userpool_id, username, attribute_name, object_url)
                return True,'File Uploaded to S3'
            except Exception as e:
                print(f"Error uploading to S3: {str(e)}")
                return False,str(e)

def get_all_sub_ids(client,user_pool_id):
    sub_ids = []

    # Initialize the Paginator for list_users API call
    paginator = client.get_paginator('list_users')
    page_iterator = paginator.paginate(UserPoolId=user_pool_id)

    # Iterate through the pages of user data
    for page in page_iterator:
        for user in page.get('Users', []):
            sub_ids.append(user['Attributes'][0]['Value'])  # Assuming sub is the first attribute

    return sub_ids

def cognito_data_uploader(client,user_pool_id,username,attribute_name,update_data):
    response = client.admin_update_user_attributes(
        UserPoolId=user_pool_id,
        Username=username,
        UserAttributes=[
            {
                'Name': attribute_name,
                'Value': update_data
            }
        ]
    )
    return response