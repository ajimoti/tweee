import logging
import requests
from django.conf import settings
from django.views.debug import ExceptionReporter
from django.utils.log import AdminEmailHandler
import os
import json

class SlackHandler(AdminEmailHandler):
    def __init__(self, webhook_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.webhook_url = webhook_url

    def emit(self, record):
        try:
            request = record.request
            subject = '%s (%s IP): %s' % (
                record.levelname,
                ('internal' if request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS
                 else 'EXTERNAL'),
                record.getMessage()
            )
        except Exception:
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
            request = None

        if record.exc_info:
            exc_info = record.exc_info
        else:
            exc_info = (None, record.getMessage(), None)

        reporter = ExceptionReporter(request, is_email=True, *exc_info)
        message = reporter.get_traceback_text()

        url = request.build_absolute_uri() if request else "N/A"

        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error: {subject[:150]}*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*URL:*\n{url[:1000]}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Level:*\n{record.levelname}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```\n{message[:2900]}```"
                    }
                }
            ]
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            # print(f"Slack API Response Status: {response.status_code}")
            # print(f"Slack API Response Content: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending to Slack: {e}")
        except Exception as e:
            print(f"Unexpected error in SlackHandler: {e}")
