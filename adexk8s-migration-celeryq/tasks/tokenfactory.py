#from pyconfig.pyconfig import Config, Stack
import os, requests
import datetime
from google.oauth2 import service_account
from google.auth.transport.requests import Request

class TokenFactory:
    """
    retrieves, stores, and manages oauth tokens for apigee management api
    """
    def __init__(self):
        self.authn, self.refresh_token, self.now, self.expires_at = self.setup_token()

    def setup_token(self):
        token_response = self.request_token()
        authn = f'Bearer {token_response["access_token"]}'
        refresh_token = token_response['refresh_token']
        now = datetime.datetime.now()
        token_duration = datetime.timedelta(0, token_response['expires_in'])
        expires_at = now + token_duration
        return authn, refresh_token, now, expires_at

    def request_token(self):
        username = os.environ.get('APIGEE_MACHINE_USERNAME')
        password = os.environ.get('APIGEE_MACHINE_PASSWORD')
        

        url = "https://harvard.login.apigee.com/oauth/token"
        grant_type = "password"
        payload = {
            'grant_type': grant_type,
            'username': username,
            'password': password
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept': 'application/json;charset=utf-8',
            'authorization': "Basic ZWRnZWNsaTplZGdlY2xpc2VjcmV0"
        }
        response = requests.post(url, headers=headers, data=payload)
        return response.json()

    @property
    def token(self):
        if self.is_expired:
            self.authn, self.refresh_token, self.now, self.expires_at = self.setup_token()
        return self.authn

    def is_expired(self):
        return datetime.datetime.now() > self.expires_at

class GoogleCloudAuthenticator:
    def __init__(self, service_account_key_paths):
        self.service_account_key_paths = service_account_key_paths
        self.scopes = ['https://www.googleapis.com/auth/cloud-platform']
        self.credentials = {}
    def _get_credentials(self):
        for itm in self.service_account_key_paths:
            if not self.credentials or not itm in self.credentials or self.credentials[itm].expired:
                self.credentials[itm]= service_account.Credentials.from_service_account_file(
                    self.service_account_key_paths[itm], scopes=self.scopes)
                self.credentials[itm].refresh(Request())
        return self.credentials
    def token(self,project_name):
        credentials = self._get_credentials()
        return credentials[project_name].token
