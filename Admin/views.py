from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse,HttpResponseBadRequest
from django.template import loader
from django.conf import settings
from django.shortcuts import redirect
import boto3,os,datetime
from weasyprint import HTML
from Admin import s3_upload
from .forms import LoginForm
import subprocess,hashlib,hmac



cognito = boto3.client('cognito-idp',region_name=os.getenv('AWS_REGION'),
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
s3 = boto3.client('s3',region_name=os.getenv('AWS_REGION'),
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
user_pool_id = settings.AWS_COGNITO_USER_POOL_ID


def test(request):
    return render(request, 'test.html',{'msg': 'Webhooks working perfectly!','text':'CI/CD pipeline will be automated!'})

def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_device = form.cleaned_data['remember_device']
            print('Username:',username)
            print('Password:', password)
            if username and password is not None:
                print('not none')
                return redirect('dashboard')
                #return JsonResponse({'success': True}, content_type='application/json', status=200)
            else:
                print('none')
                return JsonResponse({'success': False,'msg':'All fields must be filled'}, content_type='application/json', status=400)
    else:
        form = LoginForm()
    return render(request, 'login.html',{'form': form})

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
        print(sts[0])
        if sts[0] is True:
            os.remove(file)
            if not os.path.exists(file):
                print('File Removed')
                return JsonResponse({'success': True}, content_type='application/json', status=200)
        elif sts[0] is False:
            return JsonResponse({'success': False,'msg':'Error while Uploading'}, content_type='application/json', status=400)
    else:

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

def get_ordinal_suffix(day):
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return suffix

def generate(request):
    if request.method == "POST":
        username = request.POST.get('username')
        print('username:',username)
        response = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        # Initialize an empty dictionary to store the extracted attributes
        user_attributes = {}

        # Loop through the 'UserAttributes' list and extract the desired attributes
        for attribute in response['UserAttributes']:
            if attribute['Name'] in ['given_name', 'middle_name', 'name', 'nickname']:
                user_attributes[attribute['Name']] = attribute['Value']
        current_date = datetime.date.today()
        try:
            if user_attributes['given_name'] == 'C':
                user_attributes['given_name'] = 'Co-Own'
            elif user_attributes['given_name'] == 'C+':
                user_attributes['given_name'] = 'Co-Own+'
            else:
                user_attributes['given_name'] = 'UNREGED'

            data = {
                'date': current_date.strftime("%d-%m-%Y"),
                'member_name': user_attributes['name'],
                'member_type': user_attributes['given_name'],
                'member_id': user_attributes['nickname'],
                'date_detailed': current_date.strftime(f"%d{get_ordinal_suffix(current_date.day)} %B %Y"),
                'head': 'Company Letter Head',
                'director_id': '123456'
            }
        except KeyError as e:
            return JsonResponse({'success': False,'msg':'Missing Attribute:'+str(e)},content_type='application/json', status=400)
        #director signature was store in s3 : https://value1-admindashboard.s3.ap-south-1.amazonaws.com/sign.png
        #print(data)
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
        return JsonResponse({'success': status}, content_type='application/json', status=200)
    else:
        return JsonResponse({'success': False}, content_type='application/json', status=400)

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


def webhook_view(request):
    # Verify the webhook secret (if used)
    secret = "WoWoVj55BCKgGnn9My1YVydFEUAYoKJtrxrTKJMV4Nk="  # Replace with your actual secret key
    signature = request.headers.get('X-Hub-Signature')
    body = request.body.decode('utf-8')
    if not verify_webhook_signature(secret, signature, body):
        return JsonResponse({"message": "Webhook verification failed"}, status=400)

    # Handle the webhook event
    try:
        # Pull the latest code from the GitHub repository
        pull_code = subprocess.Popen(["git", "pull", "origin", "master"], cwd="/home/ubuntu/Value1-AdminDashboard/", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pull_stdout, pull_stderr = pull_code.communicate()

        if pull_code.returncode != 0:
            return JsonResponse({"message": "Failed to pull code from GitHub", "stderr": pull_stderr.decode('utf-8')}, status=500)

        # Restart Supervisor and Nginx
        restart_supervisor = subprocess.Popen(["sudo", "supervisorctl", "restart", "guni:*"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        restart_supervisor.wait()

        restart_nginx = subprocess.Popen(["sudo", "systemctl", "restart", "nginx"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        restart_nginx.wait()

        if restart_supervisor.returncode != 0 or restart_nginx.returncode != 0:
            return JsonResponse({"message": "Failed to restart Supervisor or Nginx",
                                 "supervisor_stderr": restart_supervisor.stderr.decode('utf-8'),
                                 "nginx_stderr": restart_nginx.stderr.decode('utf-8')}, status=500)

        return JsonResponse({"message": "Webhook received and processed successfully"})

    except Exception as e:
        return JsonResponse({"message": f"An error occurred: {str(e)}"}, status=500)

def verify_webhook_signature(secret, signature, body):
    # Verify the webhook signature (GitHub sends it in the X-Hub-Signature header)
    if not signature or not body:
        return False

    expected_signature = "sha1=" + hmac.new(secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha1).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
