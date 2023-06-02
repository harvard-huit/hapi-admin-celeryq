try:
    from .tokenfactory import TokenFactory, GoogleCloudAuthenticator
except:
    from tokenfactory import TokenFactory, GoogleCloudAuthenticator
from pprint import pprint
from copy import deepcopy, copy
import requests, json
from googleapiclient import discovery
from google.oauth2 import service_account
from urllib.parse import urlencode

class apigeeXPrincipal():
    def __init__(self,project_name,service_account_key_paths):
        self.project_name=project_name
        self.service_account_key_paths=service_account_key_paths
        self.service=self.__getService__()
        self.xTokenFactory=GoogleCloudAuthenticator(service_account_key_paths)
        self.base_edge_url= "https://api.enterprise.apigee.com/v1/organizations"
        self.base_x_url="https://apigee.googleapis.com/v1/organizations"
    def __getService__(self):
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_key_paths[self.project_name],
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )

        # Create the service client
        service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
        return service


    def processRequest(self,url,headers,method='get',params=None,data=None):
        #headers = {"Authorization": f"Bearer {self.tokenfactory.token()}"}
        if method.lower()== 'get':
            req=requests.get(url,headers=headers,params=params)
        elif method.lower()== 'post':
            req=requests.post(url,data=json.dumps(data),headers=headers,params=params)
        elif method.lower()== 'put':
            req=requests.put(url,data=json.dumps(data),headers=headers)
        elif method.lower()=='delete':
            req=requests.delete(url,headers=headers)
        else:
            raise Exception("Method must be get or put or post or delete")
        try:
            result=req.json()
        except:
            result={"status_code":req.status_code,"text":req.text}
        return result
    def getXPrincipal(self,principal_email=None):
        
        if principal_email:
            url=f"{self.base_x_url}/{self.project_name}/principals/{principal_email}"
        else:
            url = f"{self.base_x_url}/{self.project_name}/principals"
        headers = {
            "Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}",
            "Content-Type": "application/json"}
        return self.processRequest(url,headers)

    def add_principle_to_project(self,project_id,principal_email, tenant_name):
        
        # Set the API endpoint URL
        url = f"{self.base_x_url}/{self.project_name}/principals"

        # Set the headers with the access token and content type
        headers = {
            "Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}",
            "Content-Type": "application/json"}
        # Set the payload with the principle email
        payload = {
            "email": principal_email,
            "roles": [
                {
                    "role": "roles/apigee.role.viewer"  # Replace with the desired role
                }
            ],
            "conditions": [
                f"""((resource.type == "apigee.googleapis.com/SharedFlowRevision" && 
                resource.name.startsWith('organizations/{project_id}/sharedflows/{tenant_name}-') || 
                resource.type == "apigee.googleapis.com/SharedFlow" && 
                resource.name.startsWith('organizations/{project_id}/sharedflows/{tenant_name}-') || 
                resource.type == "apigee.googleapis.com/ProxyRevision" && 
                resource.name.startsWith('organizations/{project_id}/apis/{tenant_name}-') ||
                resource.type == "apigee.googleapis.com/Proxy" && 
                resource.name.startsWith('organizations/{project_id}/apis/{tenant_name}-') ||
                (resource.type == "apigee.googleapis.com/ApiProduct" &&
                resource.name.startsWith("organizations/{project_id}/apiproducts/{tenant_name}-"))) && 
                resource.service == "apigee.googleapis.com")|| 
                resource.service != "apigee.googleapis.com"|| 
                resource.type == "cloudresourcemanager.googleapis.com/Project"
                """ 
                ]
        }
        
        # Send a POST request to add the principle to the project
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Check the response status code
        if response.status_code == 200:
            print("Principle added successfully.")
        else:
            print(f"Failed to add principle. Status code: {response.status_code}")
            print(response.text)

    def search_google_groups(self,customer_id):
        service = discovery.build('admin', 'directory_v1', credentials=credentials)
        search_query = urlencode({
                "query": f"parent=='customerId/{customer_id}' && 'cloudidentity.googleapis.com/groups.discussion_forum' in labels"})
        search_group_request = self.service.groups().search()
        param = "&" + search_query
        search_group_request.uri += param
        response = search_group_request.execute()

        return response

            
