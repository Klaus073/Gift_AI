from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
from paapi5_python_sdk.rest import ApiException
import os
import json
from cache_service import get_cached_response
 
access = os.environ.get('ACCESS_KEY')
 
secret = os.environ.get('SECRET_KEY')
 
partner = os.environ.get('PARTNER_TAG')
 
 
def search_items(product ,type):
    # print("1. ",keyword, "2. ",category,"3. ",budget_value)
    # print("Product :", product)
    # min = int(min)
    # max = int(max)
    # # print("maxprice", budget)
    # print("min",min,type(min))
    # print("max",max,type(max))
 
    access_key = access
    secret_key = secret
    partner_tag = partner
 
    host = "webservices.amazon.com"
    region = "us-east-1"
 
    default_api = DefaultApi(access_key=access_key, secret_key=secret_key, host=host, region=region)
    if product == '':
        keywords = "gift items"
    keywords = product
 
    """ Specify the category in which search request is to be made """
    """ For more details, refer: https://webservices.amazon.com/paapi5/documentation/use-cases/organization-of-items-on-amazon/search-index.html """
    # if category == "":
    #     category = "All"
    search_index ="All"
 
 
 
 
    """ Specify item count to be returned in search result """
    if type == "list":
        item_count = 1
    else:
        item_count = 4
 
    """ Choose resources you want from SearchItemsResource enum """
    """ For more details, refer: https://webservices.amazon.com/paapi5/documentation/search-items.html#resources-parameter """
    search_items_resource = [
        SearchItemsResource.ITEMINFO_TITLE,
        SearchItemsResource.OFFERS_LISTINGS_PRICE,
        SearchItemsResource.IMAGES_PRIMARY_LARGE,
        SearchItemsResource.ITEMINFO_BYLINEINFO,
        SearchItemsResource.ITEMINFO_FEATURES,
        SearchItemsResource.OFFERS_LISTINGS_AVAILABILITY_MESSAGE,
        SearchItemsResource.BROWSENODEINFO_BROWSENODES_SALESRANK
 
    ]
 
    """ Forming request """
    try:
        search_items_request = SearchItemsRequest(
 
            partner_tag=partner_tag,
            partner_type=PartnerType.ASSOCIATES,
            keywords=keywords,
            search_index=search_index,
            item_count=item_count,
            resources=search_items_resource
        )
    except ValueError as exception:
        print("Error in forming SearchItemsRequest: ", exception)
        return
 
    try:
 
        """ Sending request """
        # NOTE - Check if response exists in cache, return if it does otherwise send request to paapi
        response = get_cached_response(search_items_request, default_api.search_items)
       
        if response.errors is not None:
            print("\nPrinting Errors:\nPrinting First Error Object from list of Errors")
            print("Error code", response.errors[0].code)
            print("Error message", response.errors[0].message)
 
    except ApiException as exception:
        print("Error calling PA-API 5.0!")
        print("Status code:", exception.status)
        print("Errors :", exception.body)
        print("Request ID:", exception.headers["x-amzn-RequestId"])
 
    except TypeError as exception:
        print("TypeError :", exception)
 
    except ValueError as exception:
        print("ValueError :", exception)
 
    except Exception as exception:
        print("Exception :", exception)
 
    return response
 
 
def simplify_json(json_obj):
    result = {}
 
    def flatten(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}_{key}" if prefix else key
                flatten(value, new_key)
        else:
            result[prefix] = obj
 
    flatten(json_obj)
    return result
 
 
def getitems(product   ):
    api_output = simplify_json(search_items(product ))
    api_output=api_output[""]
    api_output_dict= api_output.to_dict()
    return api_output_dict
 
default = ["god of war","spider man : miles morales" ]
def multiple_items(products  ):
    all_prod =[]
    if isinstance(products, list):
       
        for i in products:
            prod = search_items(i , "list")
            all_prod.append(prod.get('search_result').get('items')[0])
        products_json = {
        "search_result": {
            "items": all_prod,
            "total_result_count": len(all_prod)
            }
                }
        return products_json
    else:
        prod = search_items(products , "str")
 
        return prod