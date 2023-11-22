import redis
import json
import hashlib
import requests
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest

# Initialize Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

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

def get_cached_response(search_items_params, send_req):
    # Generate a unique cache key from the request parameters
    keys_to_use = search_items_params.keywords.lower() + search_items_params.search_index.lower()
    cache_key = hashlib.md5(str(keys_to_use).encode('utf-8')).hexdigest()

    # Check if the response is already in the cache
    cached_response = redis_client.get(cache_key)
    if cached_response:
        return json.loads(cached_response)
    else:
        # NOTE -- Make the request
        response = send_req(search_items_params)
        

        serialized_res = simplify_json(response)
        api_output=serialized_res[""]
        api_output_dict= api_output.to_dict()

        # Cache the response in Redis with a TTL (time-to-live)
        redis_client.set(cache_key, json.dumps(api_output_dict), 3600) # Cache for 1 hour

        # Print the response
        return api_output_dict


# def test(asd):
#     print("sending request")
#     return dict(text= "hello world", random_field= "Hola there")

# print(get_cached_response(dict(keywords= "harry potter", search_index="Books"), test))
