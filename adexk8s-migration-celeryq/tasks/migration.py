from tokenfactory import TokenFactory, GoogleCloudAuthenticator
from pprint import pprint
from copy import deepcopy, copy


import requests, json

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
    def getProducts(self,product=None):
        if product:
            url=f"https://api.enterprise.apigee.com/v1/organizations/{self.org_name}/apiproducts/{product}"
        else:
            url=f"https://api.enterprise.apigee.com/v1/organizations/{self.org_name}/apiproducts"
        headers = {
                'Authorization': self.tokenfactory.token,
                'Accept': 'application/json'
            }
        req=requests.get(url,headers=headers)
        return req.json()
    def appDetails(self,api_product,hide_keys=True):
        endpoint_url = f"https://api.enterprise.apigee.com/v1/organizations/{self.org_name}/apps"
        developers_endpoint_url = f"https://api.enterprise.apigee.com/v1/organizations/{self.org_name}/developers"
        # Set the headers
        headers = {"Authorization": f"{self.tokenfactory.token}"}
        req=requests.get(endpoint_url,headers=headers)
        apps=req.json()
        all_apps=[]
        for app in apps:
            detail_app= requests.get(endpoint_url + f"/{app}",headers=headers)
            detail_app=detail_app.json()
            match=list(filter(lambda d: list(filter(lambda i: api_product == i['apiproduct'] , d['apiProducts'])), detail_app['credentials']))
            if match:
                req=requests.get(developers_endpoint_url + f"/{detail_app['developerId']}",headers=headers)
                detail_app['developer']=req.json()
                if hide_keys:
                    for key in detail_app['credentials']:
                        key['consumerKey']="****"
                        key['consumerSecret']="****"


                # developers=[]
                all_apps.append(detail_app)
        return all_apps
        
    def list_products_with_apps_developers_for_proxy(self, proxy_name,hide_keys=True):
        # Set the endpoint URLs
        products_endpoint_url = f"https://api.enterprise.apigee.com/v1/organizations/{self.org_name}/apiproducts"
        apps_endpoint_url = "https://api.enterprise.apigee.com/v1/organizations/{self.org_name}/developers/{developer_email}/apps"

        # Set the headers
        headers = {"Authorization": f"{self.tokenfactory.token}"}

        # Send the GET request to retrieve the list of products
        products_response = requests.get(products_endpoint_url, headers=headers)
        products = products_response.json()

        # Loop through the products to get the list of apps for the proxy
        result={"proxy_name":proxy_name,"products":[]}
        for product_name in products:
            req=requests.get(products_endpoint_url + f"/{product_name}",headers=headers)
            product=req.json()
            if proxy_name in product["proxies"]:
                product['apps']=self.appDetails(product_name,hide_keys)
                result['products'].append(product)
        return result

class apigeeXManagementAPI():
    def __init__(self,org_name,project_name,service_account_key_paths):
        self.org_name=org_name
        self.project_name=project_name
        self.edgeTokenFactory=TokenFactory()
        self.xTokenFactory=GoogleCloudAuthenticator(service_account_key_paths)
        self.current_project=None
        self.base_edge_url= "https://api.enterprise.apigee.com/v1/organizations"
        self.base_x_url="https://apigee.googleapis.com/v1/organizations"

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
    def batchMigrateProducts(self):
        products=self.getEdgeProducts()
        result={"Created":0,"Updated":0}
        for itm in products['apiProduct']:
            res,method=self.setXProduct(itm)
            if method=='put':
                result["Updated"]=result["Updated"] + 1
            else:
                result["Created"]=result["Created"] + 1
        return result
    def getEdgeProducts(self,product=None):
        if product:
            endpoint_url=f"{self.base_edge_url}/{self.org_name}/apiproducts/{product}?expand=true"
        else:
            endpoint_url=f"{self.base_edge_url}/{self.org_name}/apiproducts?expand=true"
        headers = {
                'Authorization': self.edgeTokenFactory.token,
                'Accept': 'application/json'
            }
        params = {"expand": True}
        data=self.processRequest(endpoint_url,headers,params=params)
        return data
    def getXProducts(self,product=None):
        getOperations=False
        if product:
            endpoint_url=f"{self.base_x_url}/{self.project_name}/apiproducts/{product}"
            getOperations=True
        else:
            endpoint_url=f"{self.base_x_url}/{self.project_name}/apiproducts"
        headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
        data=self.processRequest(endpoint_url,headers)
        return data
    def setXProduct(self,data,tenant="adex"):
        endpoint_url=f"{self.base_x_url}/{self.project_name}/apiproducts"
        headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
        product_payload = {
            'name': data['name'],
            'displayName': data.get('displayName', ""),
            'description': data.get('description', ""),
            'apiResources': data.get('apiResources', ["/"]),
            'environments': [],
            'proxies': data.get('proxies', []),
            'quota': data.get('quota',None),
            'quotaInterval': data.get('quotaInterval',None),
            'quotaTimeUnit': data.get('quotaTimeUnit',None),
            'approvalType': data.get('approvalType',None),
            'attributes': data.get('attributes',None)
        }
        method='post'
        existing_products=self.getXProducts()
        if 'apiProduct' not in existing_products:
            existing_products['apiProduct']=[]
        if self.filter_dicts_by_key_value('name', product_payload['name'], existing_products['apiProduct']):
            endpoint_url=f"{self.base_x_url}/{self.project_name}/apiproducts/{product_payload['name']}"
            method='put'
        result=self.processRequest(endpoint_url,headers,method=method,data=product_payload)
        return result,method
    def filter_dicts_by_key_value(self,key, value, list_of_dicts):
        """
        Helper Funciton
        """
        filtered_list = list(filter(lambda d: d.get(key) == value, list_of_dicts))
        return filtered_list
    def getEdgeDevelopers(self,developers_email=None):
        """
        Function will return a list of all developers
        Args: org_name (str)
        Result: list of developers emails
        """
        if developers_email:
            endpoint_url = f"{self.base_edge_url}/{self.org_name}/developers/{developers_email}"
        else:
            endpoint_url = f"{self.base_edge_url}/{self.org_name}/developers"
        headers = {"Authorization": f"{self.edgeTokenFactory.token}"}
        data=self.processRequest(endpoint_url,headers)
        if not developers_email:
            data=list(filter(lambda k: 'devteam.apigee.io' not in k, data))
        return data
    def getXDevelopers(self,developers_email=None):
        if developers_email:
            endpoint_url = f"{self.base_x_url}/{self.project_name}/developers/{developers_email}"
        else:
            endpoint_url = f"{self.base_x_url}/{self.project_name}/developers"
        headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
        data=self.processRequest(endpoint_url,headers)
        return data
    def getEdgeTeams(self):
        endpoint_url = f"{self.base_edge_url}/{self.org_name}/teams"
        headers = {"Authorization": f"{self.edgeTokenFactory.token}"}
        data=self.processRequest(endpoint_url,headers)
        return data
    def batchMigrateDeveloper(self):
        devs=self.getEdgeDevelopers()
        results={"created":0,"updatedExisted":0,"otherErrors":0}
        for dev in devs:
            developer_account=self.getEdgeDevelopers(dev)
            data=self.setXDeveloper(developer_account)
            if 'error' in data:
                if data['error']['code']==409:
                    results["updatedExisted"]=results["updatedExisted"] +1
                else:
                    results["otherErrors"]=results["otherErrors"] +1
            else:
                results["created"]=results["created"] +1
        return results
    def setXDeveloper(self, data):
        endpoint_url = f"{self.base_x_url}/{self.project_name}/developers"
        headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
        #Clean up Edge to X
        data=self.cleanupEdge2X(data)
        method='post'
        existing_developer=self.getXDevelopers(developers_email=data['email'])
        if 'email' in existing_developer:
            endpoint_url=f"{self.base_x_url}/{self.project_name}/developers/{data['email']}"
            method='put'
        data=self.processRequest(endpoint_url,headers,method=method,data=data)
        #pprint(data)
        return data
    def setSingleXApp(self,developer_email,app_name):
        app=self.getEdgeApps(developer_email,app_name)
        data=self.setXApp(developer_email,app)
        data=self.getXApps(developer_email,app_name)
        #Delete new keys
        if 'credentials' in data:
            for key in data['credentials']:
                self.deleteXKey(app_name,developer_email,key['consumerKey'])
        #Add Edge Keys
        self.setXKey(app_name,developer_email)
        return self.getXApps(developer_email,app_name)
        
    def batchMigrateApps(self):
        """
        Migrate entire list of Apps for all Developers
        """
        devs=self.getEdgeDevelopers()
        results={"developersCreatedUpdated":0,"error":0}
        for dev in devs:
            apps=self.getEdgeApps(dev)
            for app in apps['app']:
                data=self.setSingleXApp(dev,app['name'])
                if 'error' in data:
                    results["error"]=results["error"] +1
                    # if data['error']['code']==409:
                    #     results["alreadyExisted"]=results["alreadyExisted"] +1
                    # else:
                    #     results["otherErrors"]=results["otherErrors"] +1
                    #     print(data)
                else:
                    results["developersCreatedUpdated"]=results["developersCreatedUpdated"] +1
        return results
    def cleanupEdge2X(self,data):
        """
        Helper function to clean up Edge to X attributes
        """
        for itm in ["lastModifiedBy","createdBy"]:
            if itm in data:
                del data[itm]
        if 'email' in data:
            data["email"]=data["email"].lower()
        return data
    def getEdgeApps(self,developer_email,app_name=None):
        """
        Returns individual or list of Apps from Apigee Edge
        :params developer_email string developer email
        :params app_name string Optional app name 
        """
        if app_name:
            endpoint_url = f"{self.base_edge_url}/{self.org_name}/developers/{developer_email}/apps/{app_name}?expand=true"
        else:
            endpoint_url = f"{self.base_edge_url}/{self.org_name}/developers/{developer_email}/apps?expand=true"
        headers = {"Authorization": f"{self.edgeTokenFactory.token}"}
        data=self.processRequest(endpoint_url,headers)
        #pprint(data)
        return data
    def getXApps(self,developer_email,app_name=None):
        """
        Returns individual or list of Apps from Apigee X
        :params developer_email string developer email
        :params app_name string Optional app name 
        """
        if app_name:
            endpoint_url = f"{self.base_x_url}/{self.project_name}/developers/{developer_email}/apps/{app_name}"
        else:
            endpoint_url = f"{self.base_x_url}/{self.project_name}/developers/{developer_email}/apps"
        headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
        
        data=self.processRequest(endpoint_url,headers)
        return data
    def setXApp(self,developer_email, data):
        """
        Create the new App in Apigee X
        :params developer_email string developer email
        :params data object App data from Apigee 
        """
        endpoint_url = f"{self.base_x_url}/{self.project_name}/developers/{developer_email}/apps"
        headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
        method='post'
        existing_apps=self.getXApps(developer_email)
        if 'app' in existing_apps:
            if self.filter_dicts_by_key_value('appId', data['name'], existing_apps['app']):
                endpoint_url=f"{self.base_x_url}/{self.project_name}/apiproducts/{data['name']}"
                method='put'
        #Clean up Edge to X
        data=self.cleanupEdge2X(data)
        result=self.processRequest(endpoint_url,headers,method=method,data=data)
        return result
    def getDisplayName(self,app_data):
        """
        Get the Display Name
        params: app_data object 
        """
        displayName=""
        for itm in app_data['attributes']:
            if itm['name']=="DisplayName":
                displayName= itm['value']
        return displayName
        
    def setXKey(self,app_name,developer_email):
        """
        Migrates App Keys from Apigee Edge to Apigee X
        :params app_name string This is th app name.
        :params developer_email string developer email
        Return: the update Apigee X App 
        """
        endpoint_url = f"{self.base_x_url}/{self.project_name}/developers/{developer_email}/apps/{app_name}/keys"
        headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
        #Clean up Edge to X
        data=self.getEdgeApps(developer_email,app_name)
        data=self.cleanupEdge2X(data)
        for itm in data['credentials']:
            # Get Status of Product
            product_status=itm['apiProducts']
            #Change Products to list of strings (name of product)
            products=[]
            for apiproduct in itm['apiProducts']:
                products.append(apiproduct['apiproduct'])
            keys=deepcopy(itm)
            keys["apiProducts"]=products
            # Add Credentials
            result=self.processRequest(endpoint_url,headers,method='post',data=keys)
            #Update the apiProducts
            result['apiProducts']=products
            endpoint_url=f"{endpoint_url}/{itm['consumerKey']}"
            result=self.processRequest(endpoint_url,headers,method='put',data=result)
            for status in product_status:
                url=f"{endpoint_url}/apiproducts/{status['apiproduct']}"
                #print(url)
                if status['status'] != "pending": 
                    if status['status'].lower()=='approved':
                        params = {"action": 'approve'}
                    else:
                        params = {"action": 'revoke'}
                    self.processRequest(url,headers,method='post',params=params,data={})
        # Return the finalized XApp
        data=self.getXApps(developer_email,app_name)
        return data
    def deleteXKey(self,app_name,developer_email,key):
        """
        Delete the Apigee X App Key
        :params app_name string This is th app name.
        :params developer_email string developer email
        :params key string  key to be deleted
        """
        endpoint_url = f"{self.base_x_url}/{self.project_name}/developers/{developer_email}/apps/{app_name}/keys/{key}"
        headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
        result=self.processRequest(endpoint_url,headers,method='delete')
        return result
    def batchDeleteDevelopers(self,developer_email=None):
        if developer_email:
            devs={}
            devs['developer']=[developer_email]
        else:
            devs = self.getXDevelopers()
        for dev in devs['developer']:
            endpoint_url = f"{self.base_x_url}/{self.project_name}/developers/{dev['email']}"
            headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
            data=self.processRequest(endpoint_url,headers,method='delete',data={})
            print(data)
        result={"deletedDevelopers":len(devs["developer"])}
        return result
    def batchDeleteProducts(self):
        products=self.getXProducts()
        for itm in products["apiProduct"]:
            endpoint_url=f"{self.base_x_url}/{self.project_name}/apiproducts/{itm['name']}"
            headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
            self.processRequest(endpoint_url,headers,method='delete',data={})
        result={"deletedProducts":len(products["apiProduct"])}
        return result
    def batchDeleteApps(self):
        """
        Delete all Apps for all Developers
        """
        devs=self.getXDevelopers()
        results={"deletedApps":0}
        for dev in devs:
            apps=self.getXApps(dev['email'])
            if 'app' in apps:
                for app in apps['app']:
                    endpoint_url = f"{self.base_x_url}/{self.project_name}/developers/{dev['email']}/apps/{app['appId']}"
                    headers = {"Authorization": f"Bearer {self.xTokenFactory.token(self.project_name)}"}
                    result=self.processRequest(endpoint_url,headers,method='delete',data={})
                    results["deletedApps"]=results["deletedApps"] +1
        return results