# -*- coding: utf-8 -*-
"""
December 19th, 2022

@author: Gillies
"""

import mailjet_rest
import os

MAILJET_API_KEY = os.environ['MAILJET_API_KEY']
MAILJET_API_SECRET = os.environ['MAILJET_API_SECRET']
MAILJET_SENDER = os.environ['MAILJET_SENDER']



def sendEmail(ip, email):
    client = mailjet_rest.Client(
        auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')

    body = f"<p>Your dashboard is live at <b><a href='{ip}'>this address</a>."
    data = {
        'Messages': [{
            "From": {
                    "Email": MAILJET_SENDER,
                    "Name": "Homemade SenseU"
            },
            "To": [
                {
                    "Email": email
                }             
            ],
            "Subject": "The Eagle Has Landed",
            "TextPart": body,
            "HTMLPart": body
        }]
    }      
    result = client.send.create(data=data)
    return result

def cors_enabled_function(request):

    request_json = request.get_json(silent=True)
    request_args = request.args

    # For more information about CORS and CORS preflight requests, see:
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

    else:

        if request_json and 'ip' in request_json:
            ip = request_json['ip']
            email = request_json['email']
         
        elif request_args and 'blue' in request_args:
            ip = request_args('ip')
            email = request_args('email')

        # Set CORS headers for the main request
        headers = {
            'Access-Control-Allow-Origin': '*'
        }

        if request.method == "POST":

            result = sendEmail(ip,  email)

        return (result.json()["Messages"][0]["Status"], result.status_code, headers)