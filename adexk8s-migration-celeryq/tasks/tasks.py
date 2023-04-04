from celery import Celery
import celeryconfig
from .migration import apigeeEdgeManagementAPI

app = Celery()
app.config_from_object(celeryconfig)


#Apigee Proxies
@app.task()
def getEdgeProxies(org_name,prefix=None):
    eapi=apigeeEdgeManagementAPI(org_name)
    result=eapi.getProxies()
    if prefix:
        result=filter(lambda x: x.startswith(prefix), result)
    return result
