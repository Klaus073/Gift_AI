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


def filter_products(products):
    filtered_products = []
    skipped_count = 0

    for product in products['search_result']['items']:
        try:
            # Check if all the required keys have non-None values
            if (
                product['images']['primary']['large']
                and product['item_info']['features']
                and product['offers']['listings'][0]['price']['display_amount']
                and product['item_info']['title']['display_value']
            ):
                filtered_products.append(product)
            else:
                skipped_count += 1
        except (KeyError, TypeError):
            print("got here")
            # Handle the case where the required keys are not present or have None values
            skipped_count += 1

    # Update the items with the filtered products
    products['search_result']['items'] = filtered_products
    print(skipped_count)
    return products



def get_item_with_lowest_sales_rank(items):
    # Initialize the variable to store the item with the lowest sales rank
    lowest_sales_rank_item = None
    items = items["search_result"]["items"]

    # Iterate through each item in the list
    try:
        for item in items:
            browse_node_info = item.get('browse_node_info')
            
            if browse_node_info is None:
                continue
            # Check if browse_node_info is None
            if browse_node_info is None:
                raise ValueError(f"Exception: browse_node_info is None for item {item}")

            # Check if 'WebsiteSalesRank' is present in browse_node_info
            if 'WebsiteSalesRank' in browse_node_info:
                website_sales_rank = browse_node_info.get('WebsiteSalesRank')

                # Check if 'SalesRank' is present and not None
                if website_sales_rank is not None and 'SalesRank' in website_sales_rank:
                    sales_rank = int(website_sales_rank['SalesRank'])

                    if lowest_sales_rank_item is None or sales_rank < lowest_sales_rank_item.get('lowest_sales_rank', float('inf')):
                        lowest_sales_rank_item = {
                            'item': item,
                            'lowest_sales_rank': sales_rank
                        }

    
        

            # Check if 'browse_nodes' key is present in 'browse_node_info'
            elif 'browse_nodes' in browse_node_info:
                # Initialize variable to store the lowest sales rank among browse nodes
                lowest_sales_rank = None

                # Iterate through each browse node
                for node in browse_node_info['browse_nodes']:
                    # Check if 'sales_rank' key is present and the value is not None
                    if 'sales_rank' in node and node['sales_rank'] is not None:
                        # Convert sales rank to integer
                        current_sales_rank = int(node['sales_rank'])

                        # Check if the current sales rank is lower than the previously found lowest
                        if lowest_sales_rank is None or current_sales_rank < lowest_sales_rank:
                            lowest_sales_rank = current_sales_rank

                # Check if there is a valid lowest sales rank among browse nodes
                if lowest_sales_rank is not None:
                    # Check if the current item has a lower sales rank than the previously found lowest
                    if lowest_sales_rank_item is None or lowest_sales_rank < lowest_sales_rank_item['lowest_sales_rank']:
                        # Update the lowest sales rank item
                        lowest_sales_rank_item = {
                            'item': item,
                            'lowest_sales_rank': lowest_sales_rank
                        }
    except TypeError as e:
        print(f"been herer")
    # Return the item with the lowest sales rank
    # items_dict = {}
    # final_list = []
    # final_list.append(lowest_sales_rank_item.get('item', {}))
    # items_dict["items"] = final_list
    return lowest_sales_rank_item.get('item', {})

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
        GetItemsResource.IMAGES_PRIMARY_LARGE
        
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
        
        SearchItemsResource.ITEMINFO_TITLE,
        SearchItemsResource.OFFERS_LISTINGS_PRICE,
        SearchItemsResource.ITEMINFO_FEATURES,
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
# def multiple_items(products):
#     # print("here")
#     all_prod = []
#     asin_list = []
#     products_json={}
#     if isinstance(products, list):
#         for i in products:
#             prod = search_items(i)
#             # print("here1")
            
#             prod_asin = get_lowest_sales_rank_asin(prod)
#             asin_list.append(str(prod_asin))
#         # print("asin",asin_list)
#         # print(len(asin_list))    
#         detailed_prod = get_items(asin_list)
        
#         serialized_detailed_prod = simplify_json(detailed_prod)
#         api_output=serialized_detailed_prod[""]
#         final_serialized_detailed_prod= api_output.to_dict()
#         # print("--------------------------")
#         # print(final_serialized_detailed_prod)
#         # print("--------------------------")
#             # print(serialized_detailed_prod)
        
        
#         item_result = final_serialized_detailed_prod.get('items_result')

#         if item_result:
#             items = item_result.get('items', [])

#             all_prod.extend(items)
#         # print(all_prod)
#         products_json = {
#             "search_result": {
#                 "items": all_prod,
#                 "total_result_count": len(all_prod)
#             }
#         }
#         # print(products_json)
#         return products_json
#     else:
#         prod = search_items(products)
#         return prod


def multiple_items(products):
    all_prod = []
    
    if isinstance(products, list):
        for i in products:
            try:
                final_item = get_item_with_lowest_sales_rank(filter_products(search_items(i)))
                all_prod.append(final_item)
            except ValueError as ve:
                # Handle the specific exception, if needed
                pass
            except Exception as e:
                # Handle the general exception, if needed
                pass
        
    products_json = {
        "search_result": {
            "items": all_prod,
            "total_result_count": len(all_prod)
        }
    }
    
    return products_json

    
# print(multiple_items(default))
# print(get_items(["0399590528"]))
# LOOKING FOR BOOKS RECOMMENDATIONS , NEW TO BOOK READING , BUDGET $500 , ANY GENRE , OPEN TO RECOMMENDATIONS
# defaul =  ['Jane Austen Quilt Kit', 'Jane Austen Silhouette Framed Art', 'Jane Austen Charm Bracelet', 'Jane Austen Themed Tea Set']
# print(multiple_items(defaul))