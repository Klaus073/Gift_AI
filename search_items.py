from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
from paapi5_python_sdk.rest import ApiException
from paapi5_python_sdk.models.get_items_resource import GetItemsResource
from paapi5_python_sdk.models.get_items_request import GetItemsRequest
from paapi5_python_sdk.models.condition import Condition

import os
import json
from cache_service import get_cached_response
 
access = os.environ.get('ACCESS_KEY')
 
secret = os.environ.get('SECRET_KEY')
 
partner = os.environ.get('PARTNER_TAG')



def get_lowest_sales_rank_asin(json_data):
    # Parse the JSON data
    data = json_data

    # Get the list of items
    items = data["search_result"]["items"]

    # Initialize variables to track the lowest sales rank and corresponding ASIN
    lowest_sales_rank = float('inf')
    lowest_sales_rank_asin = None

    for item in items:
        browse_nodes = item.get("browse_node_info", {}).get("browse_nodes", [])
        
        for node in browse_nodes:
            sales_rank = node.get("sales_rank")
            
            if sales_rank is not None:
                sales_rank = int(sales_rank)
                if sales_rank < lowest_sales_rank:
                    lowest_sales_rank = sales_rank
                    lowest_sales_rank_asin = item.get("asin", None)

    return lowest_sales_rank_asin


def get_items(item_id):
    access_key = access
    secret_key = secret
    partner_tag = partner

    host = "webservices.amazon.com"
    region = "us-east-1"

    default_api = DefaultApi(access_key=access_key, secret_key=secret_key, host=host, region=region)

    """ Request initialization"""

    """ Choose item id(s) """
    item_ids = item_id
    print(item_ids)

    """ Choose resources you want from GetItemsResource enum """
    """ For more details, refer: https://webservices.amazon.com/paapi5/documentation/get-items.html#resources-parameter """
    get_items_resource = [
        GetItemsResource.ITEMINFO_TITLE,
        GetItemsResource.OFFERS_LISTINGS_PRICE,
        GetItemsResource.ITEMINFO_FEATURES,
        GetItemsResource.IMAGES_PRIMARY_LARGE,
        GetItemsResource.IMAGES_VARIANTS_LARGE
    ]

    """ Forming request """

    response = None  # Initialize response here

    try:
        get_items_request = GetItemsRequest(
            partner_tag=partner_tag,
            partner_type=PartnerType.ASSOCIATES,
            marketplace="www.amazon.com",
            condition=Condition.NEW,
            item_ids=item_ids,
            resources=get_items_resource,
        )
    except ValueError as exception:
        print("Error in forming GetItemsRequest: ", exception)
        return
    response = None
    try:
        """ Sending request """
        response = default_api.get_items(get_items_request)

        print("API called Successfully")
        # print("Complete Response:", response)

        # """ Parse response """
        # if response.items_result is not None:
        #     print("Printing all item information in ItemsResult:")
        #     response_list = parse_response(response.items_result.items)
        #     for item_id in item_ids:
        #         print("Printing information about the item_id: ", item_id)
        #         if item_id in response_list:
        #             item = response_list[item_id]
        #             if item is not None:
        #                 if item.asin is not None:
        #                     print("ASIN: ", item.asin)
        #                 if item.detail_page_url is not None:
        #                     print("DetailPageURL: ", item.detail_page_url)
        #                 if (
        #                     item.item_info is not None
        #                     and item.item_info.title is not None
        #                     and item.item_info.title.display_value is not None
        #                 ):
        #                     print("Title: ", item.item_info.title.display_value)
        #                 if (
        #                     item.offers is not None
        #                     and item.offers.listings is not None
        #                     and item.offers.listings[0].price is not None
        #                     and item.offers.listings[0].price.display_amount is not None
        #                 ):
        #                     print(
        #                         "Buying Price: ",
        #                         item.offers.listings[0].price.display_amount,
        #                     )
        #         else:
        #             print("Item not found, check errors")

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
    return response if response and not response.errors else None
 
 
def search_items(product):
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
    
    item_count = 10
 
    """ Choose resources you want from SearchItemsResource enum """
    """ For more details, refer: https://webservices.amazon.com/paapi5/documentation/search-items.html#resources-parameter """
    search_items_resource = [
        
        SearchItemsResource.IMAGES_PRIMARY_LARGE,
        
        
        
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
        # print(response)
       
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
 
default = ["SPIDER" ]
def multiple_items(products):
    # print("here")
    all_prod = []
    asin_list = []
    products_json={}
    if isinstance(products, list):
        for i in products:
            prod = search_items(i)
            # print("here1")
            
            prod_asin = get_lowest_sales_rank_asin(prod)
            asin_list.append(str(prod_asin))
        # print("asin",asin_list)
        # print(len(asin_list))    
        detailed_prod = get_items(asin_list)
        
        serialized_detailed_prod = simplify_json(detailed_prod)
        api_output=serialized_detailed_prod[""]
        final_serialized_detailed_prod= api_output.to_dict()
        # print("--------------------------")
        # print(final_serialized_detailed_prod)
        # print("--------------------------")
            # print(serialized_detailed_prod)
        
        
        item_result = final_serialized_detailed_prod.get('items_result')

        if item_result:
            items = item_result.get('items', [])

            all_prod.extend(items)
        # print(all_prod)
        products_json = {
            "search_result": {
                "items": all_prod,
                "total_result_count": len(all_prod)
            }
        }
        # print(products_json)
        return products_json
    else:
        prod = search_items(products)
        return prod
    
# print(multiple_items(default))
# print(get_items(["0399590528"]))
# LOOKING FOR BOOKS RECOMMENDATIONS , NEW TO BOOK READING , BUDGET $500 , ANY GENRE , OPEN TO RECOMMENDATIONS