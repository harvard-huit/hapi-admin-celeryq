from celery import Celery
import celeryconfig
try:
    from migration import apigeeEdgeManagementAPI, apigeeXManagementAPI
except:
    from .migration import apigeeEdgeManagementAPI, apigeeXManagementAPI
try:
    from principal import apigeeXPrincipal
except:
    from .principal import apigeeXPrincipal

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
def batchCreateDeveloperWorkflow(source_org,destination_project):
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
def batchCreateProductWorkflow(source_org,destination_project):
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
def batchCreateAppsWorkflow(source_org,destination_project):
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

@app.task()
def batchDeleteProductsWorkflow(source_org,destination_project):
    """
    Delete Products. 
    :params source_org string Apigee Edge Organization
    :params destination_project string Apigee X Project
    """
    service_account_key_paths={
        "apigee-x-poc-test":"/xkeys/apigee-x-poc-test.json",
        "apigee-x-poc-dev":"/xkeys/apigee-x-poc-dev.json"
        }
    api=apigeeXManagementAPI(source_org,destination_project,service_account_key_paths)
    results=api.batchDeleteProducts()
    return results

@app.task()
def batchDeleteAppsWorkflow(source_org,destination_project):
    """
    Delete Apps. 
    :params source_org string Apigee Edge Organization
    :params destination_project string Apigee X Project
    """
    service_account_key_paths={
        "apigee-x-poc-test":"/xkeys/apigee-x-poc-test.json",
        "apigee-x-poc-dev":"/xkeys/apigee-x-poc-dev.json"
        }
    api=apigeeXManagementAPI(source_org,destination_project,service_account_key_paths)
    results=api.batchDeleteApps()
    return results

@app.task()
def searchGoogleGroups(search_term,function="group_key",operator="startsWith"):
    """
    Search for Google Groups. Group must contain the service account accociate with the class.
    params: search_term (string): required; search term that will be used to search for groups.
    params: function (string): optional; Values: group_key (default), display_name
    params: operator (string): optional; Values: startsWith (default), contains 
    """
    service_account_key_paths={
        "apigee-x-poc-test":"/xkeys/apigee-x-poc-test.json",
        "apigee-x-poc-dev":"/xkeys/apigee-x-poc-dev.json"
        }
    # Dev service account associated with groups
    api=apigeeXPrincipal("apigee-x-poc-dev",service_account_key_paths)
    result=api.search_google_groups(search_term,function=function,operator=operator)
    if 'groups' in result:
        result=result['groups']
    return result  

@app.task()
def assignTenantGroupName(group_id,tenant_name):
    """Assign Group Name and Group Key
    params: group_id string format groups/{groupId}
    params: tenant_name (string): The new tenant name changes group key and name
    """
    service_account_key_paths={
        "apigee-x-poc-test":"/xkeys/apigee-x-poc-test.json",
        "apigee-x-poc-dev":"/xkeys/apigee-x-poc-dev.json"
        }
    # Dev service account associated with groups
    api=apigeeXPrincipal("apigee-x-poc-dev",service_account_key_paths)
    # Change Group Name and Key ID
    name_change=api.update_group_name(group_id,tenant_name)
    name_change=api.update_group_key(group_id,tenant_name)
    return name_change

@app.task()
def assignPrincipal2ApigeeProjects(members,tenant_name,roles=None):
    #members,roles, tenant_name
    """
    Assign Group Name and Group Key
    params: members (list): members to add to the project eg. ['group:apigee-adex@g.harvard.edu']
    params: tenant_name (string): name of tenant eg. adex
    params: roles (list): optional; roles to add to the principal eg. ['roles/apigee.apiAdminV2']
    """
    service_account_key_paths={
        "apigee-x-poc-test":"/xkeys/apigee-x-poc-test.json",
        "apigee-x-poc-dev":"/xkeys/apigee-x-poc-dev.json"
        }
    result=[]
    for env in service_account_key_paths:
        api=apigeeXPrincipal(env,service_account_key_paths)
        api.add_principle_to_project(members,tenant_name)
        result.append({"project":env,"principal":members})
    return result 