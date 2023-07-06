from googleapiclient import discovery
from google.oauth2 import service_account
from urllib.parse import urlencode
import os

class apigeeXPrincipal():
    def __init__(self,project_name,service_account_key_paths):
        self.project_name=project_name
        self.service_account_key_paths=service_account_key_paths
        self.service=self.__getService__()
        self.customer_id=os.environ.get('GOOGLE_CUSTOMER_ID')
    def __getService__(self,serviceName='cloudresourcemanager',version="v1"):
        """
        Create GCloud service.
        """
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_key_paths[self.project_name],
            scopes=['https://www.googleapis.com/auth/cloud-platform',
                    'https://www.googleapis.com/auth/cloud-identity.groups'
                    ]
        )
        # Create the service client
        service = discovery.build(serviceName, version, credentials=credentials)
        return service
    def getXPrincipal(self,principal_email=None):
        project_policy = self.service.projects().getIamPolicy(resource=self.project_name, body={"options":{"requestedPolicyVersion": 3}}).execute()
        if principal_email:
            result=[]
            for itm in project_policy['bindings']:
                for email in itm['members']:
                    if principal_email in email:
                        result.append(itm)
        else:
            result=project_policy
        return result
    def defineRoles(self):
        if 'dev' in self.project_name.lower():
            roles=['roles/apigee.apiAdminV2']
        else:
            roles=['roles/apigee.readOnlyAdmin']
        return roles
    def add_principle_to_project(self,members, tenant_name,roles=None ):
        """
        Add Principal to Apigee X Project
        params: members (list): members to add to the project eg. ['group:apigee-adex@g.harvard.edu']
        params: tenant_name (string): name of tenant eg. adex
        params: roles (list): optional; roles to add to the principal eg. ['roles/apigee.apiAdminV2']
        
        """
        if not roles:
            roles=self.defineRoles()
        project_policy = self.service.projects().getIamPolicy(resource=self.project_name, body={"options":{"requestedPolicyVersion": 3}}).execute()
        # TODO check condition with RW and RO
        # Rethinking this may be the only condition with the role passed will limit RW and RO
        condition=f"""((resource.type == "apigee.googleapis.com/SharedFlowRevision" && 
                    resource.name.startsWith('organizations/{self.project_name}/sharedflows/{tenant_name}-') || 
                    resource.type == "apigee.googleapis.com/SharedFlow" && 
                    resource.name.startsWith('organizations/{self.project_name}/sharedflows/{tenant_name}-') || 
                    resource.type == "apigee.googleapis.com/ProxyRevision" && 
                    resource.name.startsWith('organizations/{self.project_name}/apis/{tenant_name}-') ||
                    resource.type == "apigee.googleapis.com/Proxy" && 
                    resource.name.startsWith('organizations/{self.project_name}/apis/{tenant_name}-') ||
                    (resource.type == "apigee.googleapis.com/ApiProduct" &&
                    resource.name.startsWith("organizations/{self.project_name}/apiproducts/{tenant_name}-"))) && 
                    resource.service == "apigee.googleapis.com")|| 
                    resource.service != "apigee.googleapis.com"|| 
                    resource.type == "cloudresourcemanager.googleapis.com/Project"
                    """ 
        for role in roles:
            new_binding={'role':role,'members':members,'condition':{
                'expression':condition,'title':f"Tenant {tenant_name.upper()} condition",
                'description':f"Tenant {tenant_name.upper()} condition"}
            }
            project_policy['bindings'].append(new_binding)
        response = self.service.projects().setIamPolicy(resource=self.project_name, body={"policy":project_policy}).execute()
        return response
            
    def update_group_name(self,group_id,updated_name):
        """
        Update Group name
        params: group_id string format groups/{groupId}
        params: update_name string The new name
        """
        service=self.__getService__(serviceName="cloudidentity")
        group= {"displayName":updated_name }
        updated_group = service.groups().patch(name=f'{group_id}',updateMask="displayName", body=group).execute()
        return updated_group
    
    def update_group_key(self,group_id,update_name):
        """
        Update Group Key
        params: group_id string format groups/{groupId}
        params: update_name string The new key name (this is a mail name portion of key. NOT THE Entire EMAIL)
        """
        service=self.__getService__(serviceName="cloudidentity")
        group= {"groupKey":{"id":f"{update_name}@g.harvard.edu"}}
        updated_group = service.groups().patch(name=f'{group_id}',updateMask="groupKey", body=group).execute()
        return updated_group
    
    def search_google_groups(self,search_term,function="group_key",operator="startsWith"):
        """
        Search for Google Groups. Group must contain the service account accociate with the class.
        params: search_term string search term that will be used to search for groups.
        params: function (string): Available values: group_key, display_name
        params: operator string optional Available Values: startsWith, contains 
        """
        service=self.__getService__(serviceName="cloudidentity")
        search_query = urlencode({
            "query": f"(parent=='customers/{self.customer_id}' && {function}.{operator}('{search_term}'))"})
        search_group_request = service.groups().search()
        param = "&" + search_query
        search_group_request.uri += param
        response = search_group_request.execute()

        return response

            
