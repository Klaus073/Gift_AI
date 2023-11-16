from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
from paapi5_python_sdk.rest import ApiException
import os
import json

access = os.environ.get('ACCESS_KEY')

secret = os.environ.get('SECRET_KEY')

partner = os.environ.get('PARTNER_TAG')


def search_items(product , category ):
    # print("1. ",keyword, "2. ",category,"3. ",budget_value)

    
    access_key = access
    secret_key = secret
    partner_tag = partner

    host = "webservices.amazon.com"
    region = "us-east-1"

    default_api = DefaultApi(access_key=access_key, secret_key=secret_key, host=host, region=region)
    if product == '':
        keywords = "gift"
    keywords = product

    """ Specify the category in which search request is to be made """
    """ For more details, refer: https://webservices.amazon.com/paapi5/documentation/use-cases/organization-of-items-on-amazon/search-index.html """
    if category == "":
        category = "All"
    search_index = category

   

    """ Specify item count to be returned in search result """
    item_count = 4

    """ Choose resources you want from SearchItemsResource enum """
    """ For more details, refer: https://webservices.amazon.com/paapi5/documentation/search-items.html#resources-parameter """
    search_items_resource = [
        SearchItemsResource.ITEMINFO_TITLE,
        SearchItemsResource.OFFERS_LISTINGS_PRICE,
        SearchItemsResource.IMAGES_PRIMARY_MEDIUM,
        SearchItemsResource.ITEMINFO_BYLINEINFO,
        SearchItemsResource.ITEMINFO_FEATURES,
        SearchItemsResource.OFFERS_LISTINGS_AVAILABILITY_MESSAGE

    ]

    """ Forming request """
    try:
        search_items_request = SearchItemsRequest(
            
            partner_tag=partner_tag,
            partner_type=PartnerType.ASSOCIATES,
            keywords=keywords,
            search_index=search_index,
            item_count=item_count,
            resources=search_items_resource,
        )
    except ValueError as exception:
        print("Error in forming SearchItemsRequest: ", exception)
        return

    try:
        """ Sending request """
        response = default_api.search_items(search_items_request)
        

        

        # print("API called Successfully")
        # print("Complete Response:", response)

        # """ Parse response """
        # if response.search_result is not None:
        #     print("Printing first item information in SearchResult:")
        #     item_0 = response.search_result.items[0]
        #     if item_0 is not None:
        #         if item_0.asin is not None:
        #             print("ASIN: ", item_0.asin)
        #         if item_0.detail_page_url is not None:
        #             print("DetailPageURL: ", item_0.detail_page_url)
        #         if (
        #             item_0.item_info is not None
        #             and item_0.item_info.title is not None
        #             and item_0.item_info.title.display_value is not None
        #         ):
        #             print("Title: ", item_0.item_info.title.display_value)
        #         if (
        #             item_0.offers is not None
        #             and item_0.offers.listings is not None
        #             and item_0.offers.listings[0].price is not None
        #             and item_0.offers.listings[0].price.display_amount is not None
        #         ):
        #             print(
        #                 "Buying Price: ", item_0.offers.listings[0].price.display_amount
        #             )
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
 
 
def getitems(product = "gift items" , category = "All" ):
    api_output = simplify_json(search_items(product , category))
    api_output=api_output[""]
    api_output_dict= api_output.to_dict()
    return api_output_dict





