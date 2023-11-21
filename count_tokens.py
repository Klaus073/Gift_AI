

def extract_token_stats(api_response):
    print("here33")
    tokens_used = api_response['usage']['total_tokens']
    print("sda",tokens_used)
    prompt_tokens = api_response['usage']['prompt_tokens']
    completion_tokens = api_response['usage']['completion_tokens']
    successful_requests = api_response['usage']['successful_api_requests']
    total_cost = api_response['usage']['total_cost']

    return {
        'tokens_used': tokens_used,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'successful_requests': successful_requests,
        'total_cost': total_cost,
    }

# Function to process a prompt and print token statistics
