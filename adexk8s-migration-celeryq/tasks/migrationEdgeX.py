from tokenfactory import TokenFactory
import requests

class apigeeEdgeManagementAPI():
    def __init__(self,org_name):
        self.org_name=org_name
        self.tokenfactory=TokenFactory()
    def getProxies(self):
        url=f"https://api.enterprise.apigee.com/v1/organizations/{self.org_name}/apis"
        headers = {
                'Authorization': self.tokenfactory.token,
                'Accept': 'application/json'
            }
        req=requests.get(url,headers=headers)
        return req.json()