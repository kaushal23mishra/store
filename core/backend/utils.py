import base64
import datetime
import hashlib
import hmac
import uuid
from random import randint

import requests
from django.core.mail import EmailMessage
from django.template.loader import get_template
from pyfcm import FCMNotification
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from backend.models import Otp, Token, PasswordResetToken, Notification
from backend.serializers import NotificationSerializer
from core.settings import TEMPLATES_BASE_URL, CF_KEY, FSMS_KEY, FCM_KEY

push_notification_service = FCMNotification(api_key=FCM_KEY)


def send_user_notification(user, title, body, image):
    notif = Notification()
    notif.user = user
    notif.title = title
    notif.body = body
    notif.image = image

    notif.save()

    notif_data = NotificationSerializer(notif, many=False).data
    message_title = notif_data.get('title')
    message_body = notif_data.get('body')
    message_image = notif_data.get('image')
    message_time = notif_data.get('created_at')

    fcm_tokens = []
    for token in user.tokens_set.all():
        fcm_tokens.append(token.fcmtoken)

    if len(fcm_tokens) > 0:
        result = push_notification_service.notify_multiple_devices(registration_ids=fcm_tokens,
                                                                   message_title=message_title,
                                                                   message_body=message_body, data_message=
                                                                   {'image': message_image},
                                                                   extra_notification_kwargs={'image': message_image},
                                                                   sound=True)
        print(result)


def send_otp(phone):
    otp = randint(100000, 999999)
    validity = datetime.datetime.now() + datetime.timedelta(minutes=10)
    Otp.objects.update_or_create(phone=phone, defaults={"otp": otp, "verified": False, "validity": validity})

    url = "https://www.fast2sms.com/dev/bulkV2"

    querystring = {"authorization": FSMS_KEY, "variables_values": str(otp), "route": "otp", "numbers": str(phone)}

    headers = {
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    print(response.text)
    print("dkkdkdkdk")

    if response.json()['return'] == True:
        print(otp)
        return Response('otp sent successfully')
    else:
        return Response('sms service failed', 400)


def new_token():
    token = uuid.uuid1().hex
    return token


def token_response(user, fcmtoken):
    token = new_token()
    Token.objects.create(token=token, user=user, fcmtoken=fcmtoken)
    return Response('token ' + token)


def send_password_reset_email(user):
    token = new_token()
    exp_time = datetime.datetime.now() + datetime.timedelta(minutes=10)

    PasswordResetToken.objects.update_or_create(user=user,
                                                defaults={'user': user, 'token': token, 'validity': exp_time})

    email_data = {
        'token': token,
        'email': user.email,
        'base_url': TEMPLATES_BASE_URL
    }

    message = get_template('emails/reset-password.html').render(email_data)

    msg = EmailMessage('Reset Password', body=message, to=[user.email, ])
    msg.content_subtype = 'html'

    try:
        msg.send()
    except:
        pass
    return Response('reset_password_email_sent')


class IsAuthenticatedUser(BasePermission):
    message = 'unauthenticated_user'

    def has_permission(self, request, view):
        return bool(request.user)


def cfSignature(postData):
    signatureData = postData["orderId"] + postData["orderAmount"] + postData["referenceId"] + postData["txStatus"] + \
                    postData["paymentMode"] + postData["txMsg"] + postData["txTime"]

    message = bytes(signatureData, encoding='utf8')
    secret = bytes(CF_KEY, encoding='utf8')
    signature = base64.b64encode(hmac.new(secret,
                                          message, digestmod=hashlib.sha256).digest())

    return signature
