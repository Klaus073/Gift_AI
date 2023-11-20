import redis
import json
import hashlib
import requests
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest

# Initialize Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

def get_cached_response(search_items_params, send_req):
    # Generate a unique cache key from the request parameters
    keys_to_use = search_items_params.keywords.lower() + search_items_params.search_index.lower()
    cache_key = hashlib.md5(str(keys_to_use).encode('utf-8')).hexdigest()

    # Check if the response is already in the cache
    cached_response = redis_client.get(cache_key)
    if cached_response:
        print("Cached Response:")
        print(json.loads(cached_response))
        return json.loads(cached_response)
    else:
        # NOTE -- Make the request
        response = send_req(search_items_params)

        print('response',response)
        # Cache the response in Redis with a TTL (time-to-live)
        redis_client.set(cache_key, json.dumps(response), 3600) # Cache for 1 hour

        # Print the response
        print("API Response:")
        print(response)
        return response


# def test(asd):
#     print("sending request")
#     return dict(text= "hello world", random_field= "Hola there")

# print(get_cached_response(dict(keywords= "harry potter", search_index="Books"), test))
