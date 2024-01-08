from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus

def insert_global_token_stats(cost,session_id):
    # MongoDB connection details
    username = "jackmin1254"
    password = "pakpattan1254"
    cluster_address = "cluster0.3gct0io.mongodb.net"
    database_name = "Token_Stats"

    # Escape the username and password
    escaped_username = quote_plus(username)
    escaped_password = quote_plus(password)

    # Construct the MongoDB connection string
    mongo_uri = f"mongodb+srv://{escaped_username}:{escaped_password}@{cluster_address}/{database_name}"

    # Create a new client and connect to the server
    client = MongoClient(mongo_uri, server_api=ServerApi('1'))
    # print("got here1")
    try:
        # Select the database and collection
        database = client[database_name]
        collection = database.TokenStats
        # print("got here")

        existing_document = collection.find_one({"session_id": session_id})
        if existing_document:
            # If the document exists, update the 'cost' field by adding the new cost
            new_total_cost = existing_document.get("cost", 0) + cost
            collection.update_one({"session_id": session_id}, {"$set": {"cost": new_total_cost}})
            print("Document updated successfully.")
        else:
            # If the document doesn't exist, insert a new document
            new_document = {"session_id": session_id, "cost": cost}
            collection.insert_one(new_document)
            print("New document inserted successfully.")


        # Insert global_token_stats into the collection
        # result = collection.insert_one(cost,session_id)

        # Print the inserted document's ID
        # print(f"Document inserted with ID: {result.inserted_id}")

    except Exception as e:
        print(f"Error inserting document: {e}")

    finally:
        # Close the MongoDB connection
        client.close()

# Example usage
# global_token_stats = {
#     "total_tokens_used": 100,
#     "prompt_tokens_used": 50,
#     "completion_tokens_used": 50,
#     "successful_requests": 10,
#     "total_cost_usd": 25.0,
# }

# insert_global_token_stats(global_token_stats)
