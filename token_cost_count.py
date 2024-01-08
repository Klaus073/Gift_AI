def tokens_cost_count(prompt_tokens , completion_tokens):
    a = prompt_tokens * 0.00001
    b = completion_tokens * 0.00003

    return a+b