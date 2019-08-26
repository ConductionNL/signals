import json

import requests
from django.conf import settings
from django.core import validators
from requests import ConnectTimeout

from signals.apps.api.ml_tool.proxy.exceptions import GateWayTimeout


class MLToolClient:
    timeout = (10.0, 10.0)
    endpoint = '{}/predict'.format(settings.ML_TOOL_ENDPOINT)
    predict_validators = [
        validators.MinLengthValidator(limit_value=1),
        validators.ProhibitNullCharactersValidator()
    ]

    def predict(self, text):
        for validator in self.predict_validators:
            validator(text)

        try:
            data = json.dumps({'text': text})
            response = requests.post(self.endpoint, data=data, timeout=self.timeout)
        except (ConnectTimeout, ):
            raise GateWayTimeout()
        else:
            return response
