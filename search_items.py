from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
from paapi5_python_sdk.rest import ApiException
from paapi5_python_sdk.models.get_items_resource import GetItemsResource
from paapi5_python_sdk.models.get_items_request import GetItemsRequest
from paapi5_python_sdk.models.condition import Condition
import time
import os
import random
from datetime import datetime
import json
import concurrent.futures


# import logging

# # Configure the logging module
# logging.basicConfig(level=logging.INFO)
 
access = os.environ.get('ACCESS_KEY')
 
secret = os.environ.get('SECRET_KEY')


 
partner = os.environ.get('PARTNER_TAG')

# logging.info(f"Access Key: {access}")
# logging.info(f"Secret Key: {secret}")
# logging.info(f"Partner Tag Key: {partner}")
def filter_products(products):
    filtered_products = []
    skipped_count = 0
    # print("here 0")
    for product in products['search_result']['items']:
        try:
            # Check if all the required keys have non-None values
            if (
                product['images']['primary']['large']
                
                and product['offers']['listings'][0]['price']['display_amount']
                and product['item_info']['title']['display_value']
            ):
                
                filtered_products.append(product)
            else:
                # print("missing",product.get('asin'))
                skipped_count += 1
        except (KeyError, TypeError) as e:
            
            # print("got here",str(e))
            # Handle the case where the required keys are not present or have None values
            skipped_count += 1

    # Update the items with the filtered products
    products['search_result']['items'] = filtered_products
    # print(skipped_count)
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
        if lowest_sales_rank_item is None:
            # print("noneeeeeeeeeee")
            
            lowest_sales_rank_item = {
                            'item': random.choice(items),
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



 
 
def search_items(product, min , max):
    
 
    access_key = access
    secret_key = secret
    partner_tag = partner
 
    host = "webservices.amazon.com"
    region = "us-east-1"
 
    default_api = DefaultApi(access_key=access_key, secret_key=secret_key, host=host, region=region)
    if product == '':
        keywords = "gift items"
    keywords = product
 
    
    search_index ="All"
 
    
    item_count = 10
 
    search_items_resource = [
        
        SearchItemsResource.IMAGES_PRIMARY_LARGE,
        
        SearchItemsResource.ITEMINFO_TITLE,
        SearchItemsResource.OFFERS_LISTINGS_PRICE,
        SearchItemsResource.ITEMINFO_FEATURES,
        
        
        SearchItemsResource.BROWSENODEINFO_BROWSENODES_SALESRANK
 
    ]
 
    """ Forming request """
    
    try:
        search_items_request = SearchItemsRequest(
 
            partner_tag=partner_tag,
            partner_type=PartnerType.ASSOCIATES,
            title=keywords,
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
        
        thread = default_api.search_items(search_items_request, async_req=True)

        time.sleep(1)
        # print("calling title endpoint")
        response = thread.get()
        # print("got response title endpoint")
        start_time = datetime.now()
        # print("start time in search items function: ",start_time)
        # response = get_cached_response(search_items_request, default_api.search_items)
        # print(response)
        # logging.info(f"Partner Tag Key: {response}")
        if response.errors is not None:
            print("\nPrinting Errors:\nPrinting First Error Object from list of Errors")
            print("Error code", response.errors[0].code)
            print("Error message", response.errors[0].message)
            if  response.errors[0].code=="NoResults":
                # print("here")
                # time.sleep(1)
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
                    end_time = datetime.now()
                    print("end time in search items function in keywords search: ",end_time)
                    execution_time = (end_time - start_time).total_seconds()
                    if execution_time < 1:
                        delay = 1 - execution_time
                        time.sleep(delay)
                        # print("delay in search function in keywords search")
                    # print("in keyword")
                    # print(f"Execution time: {execution_time} seconds")
                    # print("calling keyword endpoint")
                    response = default_api.search_items(search_items_request)
                    # print("got response from keyword endpoint")
                    # start_time = datetime.now()
                    # print("start time in search items function in keywords search: ",start_time)
                    #  logging.info(f"Partner Tag Key: {response}")
                except ValueError as exception:
                    print("Error in forming SearchItemsRequest: ", exception)
                    return
        # end_time = datetime.now()
        # print("end time in search items function: ",end_time)
        # execution_time = (end_time - start_time).total_seconds()
        # if execution_time < 1:
        #     delay = 1 - execution_time
        #     time.sleep(delay)
        #     print("delay in search function")
        

 
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
    api_output=result[""]
    api_output_dict= api_output.to_dict()
    return api_output_dict
 
 
def getitems(product   ):
    api_output = simplify_json(search_items(product ))
    api_output=api_output[""]
    api_output_dict= api_output.to_dict()
 


def process_product(product):
    max_retries = 3
    retry_delay = 2  # seconds
    retries = 0

    while retries < max_retries:
        try:
            # Introduce a delay to avoid rate limiting
            time.sleep(2)  # Adjust the sleep duration as needed
            final_item = get_item_with_lowest_sales_rank(filter_products(simplify_json(search_items(product))))
            return final_item
        except ValueError as ve:
            # Handle the specific exception, if needed
            print("value error")
            pass
        except Exception as e:
            # Check if the exception corresponds to a 429 status code
            if '429' in str(e):
                print("Rate limit exceeded. Retrying after delay.")
                time.sleep(retry_delay)
                retries += 1
            else:
                # Handle other exceptions
                print("ee |", str(e))
                pass

    print(f"Exceeded maximum retries for product: {product}")
    return None  # Or raise an exception as needed

# Your existing code...

def remove_duplicates(products):
    unique_products = []
    seen_asins = set()

    for product in products:
        asin = product.get("asin")
        if asin not in seen_asins:
            unique_products.append(product)
            seen_asins.add(asin)

    return unique_products

def multiple_items(products, min , max):
    all_prod = []
    a = 0
    start = datetime.now()
    if isinstance(products, list):
        for i in products:
            a +=1
            try:
                # if a== 1:
                #     pass
                # else:
                #     end_time = time.time()
                #     print("end time", )

                
                search_result = search_items(i, min , max)
                # start_time = time.time()
                final_item = get_item_with_lowest_sales_rank(filter_products(simplify_json(search_result)))
                # start_time = time.time()
                # execution_time = end_time - start_time
                # print(f"Execution time in main function: {execution_time} seconds")
                all_prod.append(final_item)
                # if execution_time < 1:
                #     print("got here")
                #     delay  = 1- execution_time
                #     time.sleep(delay)
                #     print("in delay: ",delay)
            except ValueError as ve:
                # Handle the specific exception, if needed
                print("value error")
                continue
            except Exception as e:
                # Handle the general exception, if needed
                print("ee |",str(e))
                continue
        end = datetime.now()
        execution_time = (end - start).total_seconds()
        # print(f"Execution time for all products: {execution_time} seconds")
    # Replicate products randomly and shuffle if the length is not 6
    # while len(all_prod) < 6:
    #     random_product = random.choice(all_prod)
    #     all_prod.append(random_product)

    # # Shuffle the list
    # random.shuffle(all_prod)
    # print("before dupli: ",len(all_prod))
    unique_products_list = remove_duplicates(all_prod)
    # print("after dupli: ",len(unique_products_list))
    if len(unique_products_list)>6:
        six_prod = unique_products_list[:6]
    else:
        six_prod = unique_products_list
    products_json = {
        "search_result": {
            "items": six_prod,
            "total_result_count": len(six_prod)
        }
    }

    return products_json