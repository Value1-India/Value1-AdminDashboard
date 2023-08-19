from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse,HttpResponseBadRequest
from django.template import loader
from django.conf import settings
from django.shortcuts import redirect
import boto3,os
from weasyprint import HTML
from Admin import s3_upload

cognito = boto3.client('cognito-idp',region_name=os.getenv('AWS_REGION'),
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
s3 = boto3.client('s3',region_name=os.getenv('AWS_REGION'),
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))


def login(request):
    template = loader.get_template('login.html')
    return HttpResponse(template.render())

def register(request):
    template = loader.get_template('register.html')
    return HttpResponse(template.render())

def dashboard(request):
    if request.method == "POST":
        user_id = request.POST.get('user_sub')
        username = request.POST.get('user_username')
        print(username)
        bucket_name = 'value1-admindashboard'
        userpool_id = settings.AWS_COGNITO_USER_POOL_ID
        file = os.path.join(settings.TEMP_FILES, 'grantletter.pdf')
        sts = s3_upload.upload(s3_client=s3, cognito_client=cognito, sub_id=user_id, username=username,
                               bucket_name=bucket_name,
                               file=file, userpool_id=userpool_id)
        return JsonResponse({'success': True}, content_type='application/json', status=200)

    else:
        user_pool_id = settings.AWS_COGNITO_USER_POOL_ID
        response = cognito.list_users(UserPoolId=user_pool_id)
        formatted_data = []
        for user_entry in response['Users']:
            username = user_entry['Username']
            updated_Date = user_entry['UserLastModifiedDate']
            created_Date = user_entry['UserCreateDate']
            user_status = user_entry['UserStatus']
            user_attributes = {
                'username': username,
                'updated_Date': updated_Date,
                'created_Date': created_Date,
                'user_status': user_status,
            }

            for attribute in user_entry['Attributes']:
                attribute_name = attribute['Name']
                attribute_value = attribute['Value']
                user_attributes[attribute_name] = attribute_value

            formatted_data.append(user_attributes)

        return render(request, 'dashboard.html', {'users': formatted_data})

def generate(request):
    data = {
        'date': '15.09.2023',
        'member_name': 'Boopathy',
        'member_type': 'Co-Own/Student',
        'member_id': 'estmynhsbtdum',
        'fname': 'febh5nusue ttr,ssm',
        'date_detailed': '15th August 2023',
        'company_name': 'OOSH LEARNINGS',
        'head': 'Company Letter Head',

    }
    # render(request, 'grant_letter_template.html', {'data': data, 'sign': sign})
    html_content = render_to_string('grant_letter_template.html', {'data': data})
    pdf_file = HTML(string=html_content).write_pdf()
    file_name = 'grantletter.pdf'
    path = "temp"
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = os.path.join(path, file_name)
    status = False
    if pdf_file != None:
        status=True
        with open(file_path,'wb') as file:
            file.write(pdf_file)
    return JsonResponse({'status': status})

def preview(request):
    pdf_file_path = os.path.join(settings.TEMP_FILES, 'grantletter.pdf')

    if not os.path.exists(pdf_file_path):
        return JsonResponse({'status': 'File not Generated'})

    with open(pdf_file_path, 'rb') as pdf_file:
        pdf_content = pdf_file.read()

    # Create an HTTP response with the PDF content
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="preview.pdf"'

    return response

'''def upload_to_S3(request):
    selected_id = request.method['POST']
    uname = request.method['POST']
    print(selected_id,uname)
    bucket_name = 'value1-admindashboard'
    userpool_id = settings.AWS_COGNITO_USER_POOL_ID
    file = os.path.join(settings.TEMP_FILES, 'grantletter.pdf')
    sts = s3_upload.upload(s3_client=s3,cognito_client=cognito,sub_id=selected_id,username=uname,bucket_name=bucket_name,
                         file=file,userpool_id=userpool_id)
    if sts:
        return JsonResponse({'success': True}, content_type='application/json', status=200)
    else:
        return JsonResponse({'error': 'File upload to S3 failed'}, content_type='application/json', status=500)'''

'''def upload_to_S3(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_sub')
        username = request.POST.get('user_username')
        print(username)
        bucket_name = 'value1-admindashboard'
        userpool_id = settings.AWS_COGNITO_USER_POOL_ID
        file = os.path.join(settings.TEMP_FILES, 'grantletter.pdf')
        # Assuming s3_upload.upload handles the S3 upload correctly
        sts = s3_upload.upload(s3_client=s3, cognito_client=cognito, sub_id=user_id, username=username,
                               bucket_name=bucket_name,
                               file=file, userpool_id=userpool_id)
        print(sts)
        if sts:
            return JsonResponse({'success': True}, content_type='application/json', status=200)
        else:
            return JsonResponse({'error': 'File upload to S3 failed'}, content_type='application/json', status=500)

    # Handle other HTTP methods if needed
    return redirect(reversed('dashboard'))'''