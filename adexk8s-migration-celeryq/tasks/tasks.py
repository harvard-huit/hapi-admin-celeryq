from celery import Celery
import celeryconfig
from .migration import apigeeEdgeManagementAPI

app = Celery()
app.config_from_object(celeryconfig)


#Apigee Proxies
@app.task()
def getEdgeProxies(org_name,prefix=None):
    """
    List all proxies from an Apigee Organization
    Args: 
        org_name (str): Apigee Organization name
    Kwargs:
        prefix (str): filter results with prefix
    """
    eapi=apigeeEdgeManagementAPI(org_name)
    result=eapi.getProxies()
    if prefix:
        result=list(filter(lambda x: x.startswith(prefix), result))
    return result

@app.task()
def getProductsAppsbyProxy(org_name,proxy,hide_keys=True):
    """
    Task returns all products/apps/developers associated with a proxy.
    Args:
        org_name (str): Apigee Organization name,
        proxy (str): Apigee proxy name
    """
    eapi=apigeeEdgeManagementAPI(org_name)
    result=eapi.list_products_with_apps_developers_for_proxy(proxy,hide_keys=hide_keys)
    return result


