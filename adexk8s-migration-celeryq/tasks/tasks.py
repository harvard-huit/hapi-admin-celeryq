from celery import Celery
import celeryconfig
from migration import apigeeEdgeManagementAPI, apigeeXManagementAPI

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

@app.task()
def batchDeveloperWorkflow(source_org,destination_project):
    """
    Sync Developer between Apigee Edge and Apigee X
    :params source_org string Apigee Edge Organization
    :params destination_project string Apigee X Project
    """
    service_account_key_paths={
        "apigee-x-poc-test":"/xkeys/apigee-x-poc-test.json",
        "apigee-x-poc-dev":"/xkeys/apigee-x-poc-dev.json"
        }
    api=apigeeXManagementAPI(source_org,destination_project,service_account_key_paths)
    results=api.batchMigrateDeveloper()
    return results
@app.task()
def batchProductWorkflow(source_org,destination_project):
    """
    Sync Products between Apigee Edge and Apigee X
    :params source_org string Apigee Edge Organization
    :params destination_project string Apigee X Project
    """
    service_account_key_paths={
        "apigee-x-poc-test":"/xkeys/apigee-x-poc-test.json",
        "apigee-x-poc-dev":"/xkeys/apigee-x-poc-dev.json"
        }
    api=apigeeXManagementAPI(source_org,destination_project,service_account_key_paths)
    results=api.batchMigrateProducts()
    return results
@app.task()
def batchAppsWorkflow(source_org,destination_project):
    """
    Sync Apps between Apigee Edge and Apigee X
    :params source_org string Apigee Edge Organization
    :params destination_project string Apigee X Project
    """
    service_account_key_paths={
        "apigee-x-poc-test":"/xkeys/apigee-x-poc-test.json",
        "apigee-x-poc-dev":"/xkeys/apigee-x-poc-dev.json"
        }
    api=apigeeXManagementAPI(source_org,destination_project,service_account_key_paths)
    results=api.batchMigrateApps()
    return results
@app.task()
def batchDeleteDevelopersAppsWorkflow(source_org,destination_project,developer_email=None):
    """
    Delete Developers and Apps associated with Developer. 
    :params source_org string Apigee Edge Organization
    :params destination_project string Apigee X Project
    :params developer_email string optional Delete only a single Developer and associated Apps
    """
    service_account_key_paths={
        "apigee-x-poc-test":"/xkeys/apigee-x-poc-test.json",
        "apigee-x-poc-dev":"/xkeys/apigee-x-poc-dev.json"
        }
    api=apigeeXManagementAPI(source_org,destination_project,service_account_key_paths)
    if developer_email:
        results=api.batchDeleteDevelopers(developer_email)
    else:
        results=api.batchDeleteDevelopers()
    return results