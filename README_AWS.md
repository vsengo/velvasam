For a Django application using AWS services such as S3, you normally use an IAM user's access key, not the AWS root user's key.
1. Create the Access Key
Since you already have an IAM user:
1. Sign in to the AWS Console.
2. Go to IAM → Users.
3. Select your IAM username.
4. Select Security credentials.
5. Find Access keys.
6. Click Create access key.
7. For the use case, choose Other (or the option appropriate for your application), then continue.
8. Click Create access key.
AWS will show you:
Access key ID:     AKIA...
Secret access key: ...
The Access key ID is what you put in:
AWS_ACCESS_KEY_ID
The secret goes in:
AWS_SECRET_ACCESS_KEY
AWS only lets you view/download the secret access key at creation time, so save it securely.

2. For Django, don't put the keys directly in settings.py
A common setup is a .env file:

AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
AWS_STORAGE_BUCKET_NAME=my-bucket
AWS_S3_REGION_NAME=ap-southeast-1

Then in Django:
import os

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")

And do not commit .env to GitHub. Add it to .gitignore:
.env

Important: Root user vs IAM user
For your Django application, don't create an access key for the root user. AWS specifically recommends against root-user access keys. AWS Documentation

Your setup should look like:
AWS Account
│
├── Root user
│   └── Used for account-level administration
│
└── IAM User
    ├── Username/password → AWS Console
    └── Access Key ID/Secret → Django / Boto3


1. Create .env
In VS Code, right-click the folder containing manage.py → New File → name it:
.env

Put your AWS credentials inside:
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=ap-southeast-1

Don't put quotes around the values unless you specifically need them.
2. Install python-dotenv
From your Django project's terminal:
pip install python-dotenv

Then in settings.py:
from dotenv import load_dotenvimport osload_dotenv()AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")


3. Very important — protect .env
Add this to .gitignore:
.env

Then check:
git status

You should not see .env listed as a file to commit.
=================================
Almost. Your Django settings are close, but I would check a few things before testing SES.
1. Your settings.py configuration
This part is reasonable:
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_SES_REGION_NAME = os.environ.get(    'AWS_SES_REGION_NAME',    'us-east-1')AWS_SES_REGION_ENDPOINT = os.environ.get(    'AWS_SES_REGION_ENDPOINT',    'email.us-east-1.amazonaws.com')
DEFAULT_FROM_EMAIL = os.environ.get(    'DEFAULT_FROM_EMAIL',    'no-reply@velvasam.net')

if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:    
    EMAIL_BACKEND = 'django_ses.SESBackend'
else:    
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


But make sure os is imported near the top of settings.py:
import os


2. Your .env should contain
Since your settings use these names, your .env should have:
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SES_REGION_NAME=us-east-1
AWS_SES_REGION_ENDPOINT=email.us-east-1.amazonaws.com
DEFAULT_FROM_EMAIL=no-reply@velvasam.net

However, there's one important issue: os.environ.get() does not automatically read a .env file.

If you are using python-dotenv, make sure you have:
from dotenv import load_dotenvload_dotenv()


near the top of settings.py, before these AWS settings are read:
import osfrom dotenv import load_dotenvload_dotenv()


Otherwise your .env can exist but Django won't necessarily load those values.

3. Make sure django-ses is installed
Your backend:
EMAIL_BACKEND = 'django_ses.SESBackend'


requires the django-ses package.

Check:
pip show django-ses

If it isn't installed:
pip install django-ses

Then check that requirements.txt contains it.

4. AWS SES has two important requirements
Even if your Django configuration is perfect, SES can reject the email if the AWS side isn't ready.

Your DEFAULT_FROM_EMAIL is:
no-reply@velvasam.net

You need to verify either that specific email address or the velvasam.net domain as an SES verified identity. AWS requires the sending identity to be verified. AWS Documentation

Also, if your SES account is still in the sandbox, the recipient must also be verified. 
AWS Documentation

5. Check that your IAM user can send SES email
The IAM user whose access key you're using needs permission such as:
ses:SendEmail

AWS documents ses:SendEmail and ses:SendRawEmail as the relevant permissions for sending. AWS Documentation
6. Then test from Django
Once those are set up, run:
python manage.py shell

Then:
from django.core.mail import send_mail
send_mail(
        "Test email from Django",    
        "This is a test email sent through Amazon SES.",    
        None,    
        ["your-email@example.com"],    
        fail_silently=False,
)

If everything is configured correctly, Django should send through SES.
One thing I'd check first
Before doing the test, run:
python manage.py shell

and:
from django.conf import settings
print(settings.EMAIL_BACKEND)
print(settings.AWS_ACCESS_KEY_ID)
print(settings.DEFAULT_FROM_EMAIL)
print(settings.AWS_SES_REGION_NAME)


You should see:
django_ses.SESBackend
AKIA...
no-reply@velvasam.net
us-east-1

Don't paste your actual secret key here.

If EMAIL_BACKEND instead shows:
django.core.mail.backends.console.EmailBackend

then Django isn't loading your AWS credentials from .env, and we should fix that before testing.



Now, for AWS SES,  create identities

What you should see
Look for something like:

Identities
Create identity

Click Create identity → choose:
Identity type
○ Domain
● Email address

Email address
no-reply@velvasam.net

Then Create identity.

After AWS sends the verification email, click the verification link. AWS says the verification email normally arrives within about five minutes. AWS Documentation

Then repeat for:
your-email@example.com

Once both are verified, we can run your Django test again.
