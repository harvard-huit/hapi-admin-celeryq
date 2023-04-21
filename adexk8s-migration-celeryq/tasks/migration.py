from .tokenfactory import TokenFactory
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
        