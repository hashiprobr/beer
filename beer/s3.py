import hmac
import json

from base64 import b64encode
from datetime import timezone, datetime, timedelta
from hashlib import sha256

from django.conf import settings


def sign(key, msg):
    return hmac.digest(key, msg, sha256)


def sign_post(bucket, key, redirect):
    now = datetime.now(timezone.utc)
    then = now + timedelta(minutes=1)
    date_time = now.strftime('%Y%m%dT%H%M%SZ')
    date = date_time[:8]

    fields = {
        'x-amz-algorithm': 'AWS4-HMAC-SHA256',
        'x-amz-credential': '{}/{}/{}/s3/aws4_request'.format(settings.AWS_ACCESS_KEY_ID, date, settings.AWS_S3_REGION_NAME),
        'x-amz-date': date_time,
        'success_action_redirect': redirect,
    }

    policy = {
        'expiration': then.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'conditions': [
            {'bucket': bucket},
            ['eq', '$key', key],
        ],
    }
    policy['conditions'].extend([{k: v} for k, v in fields.items()])

    string_to_sign = b64encode(json.dumps(policy).encode('utf-8'))
    secret_access_key = 'AWS4' + settings.AWS_SECRET_ACCESS_KEY
    date_key = sign(secret_access_key.encode('utf-8'), date.encode('utf-8'))
    date_region_key = sign(date_key, settings.AWS_S3_REGION_NAME.encode('utf-8'))
    date_region_service_key = sign(date_region_key, b's3')
    signing_key = sign(date_region_service_key, b'aws4_request')
    signature = sign(signing_key, string_to_sign)

    body = {
        'action': '{}/{}'.format(settings.AWS_S3_ENDPOINT_URL, bucket),
        'key': key,
        'policy': string_to_sign.decode('utf-8'),
        'x-amz-signature': signature.hex(),
    }
    body.update(fields)

    return body
