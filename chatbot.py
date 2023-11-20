import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from token_stats_db import insert_global_token_stats
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import json
from langchain.callbacks import get_openai_callback
from search_items import getitems
import tiktoken
api_key = os.environ.get('OPENAI_API_KEY')
llm = ChatOpenAI(openai_api_key=api_key)
memory_dict = {}
# global_token_stats = {
#     "total_tokens_used": 0,
#     "prompt_tokens_used": 0,
#     "completion_tokens_used": 0,
#     "successful_requests": 0,
#     "total_cost_usd": 0.0,
# }
COUNTER = 0

# Get the absolute path to the directory of the script or notebook
current_directory = os.path.dirname(os.path.abspath(__file__))

# Specify the path to your JSON file in the 'data' folder
file_path = os.path.join(current_directory, 'data', 'Categories_and_Subcategories.json')

with open(file_path, 'r') as file:
    data = json.load(file)

def get_or_create_memory_for_session(session_id):
    if session_id not in memory_dict:
        memory_dict[session_id] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return memory_dict[session_id]

def initial_chat(user_input, session_memory):
    
    prompt_rough = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                """
                    **Role:**
                    - Embody the persona of "THINK GIFT," a friendly assistant dedicated to helping users discover the perfect gift.
                    - Engage users in lively conversations, posing follow-up questions, and understanding their gift preferences.
                    - Maintain a positive and helpful tone, playing the role of a virtual gift advisor.

                    **Example Follow-up Questions:**
                    1. What budget range are you considering for the gift?
                    2. Who is the lucky recipient of the gift?
                    3. Share any specific interests or requirements for the product.
                    4. Could you provide the age of the user or recipient?

                    **Let's Do It Step by Step:**

                    **1. Ensure User Understanding:**
                    - Ask one follow-up question at a time to maintain a conversational flow.
                    - Avoid a strict one-question-at-a-time structure but limit the number of questions asked per interaction to one.
                    - If a user's input suggests adult preferences, offer assistance accordingly.
                    - Assume the existence of a user-requested unfamiliar product, proceeding with information gathering.

                    **2. Follow-up Questioning with Record:**
                    - Engage in follow-up questions to understand user preferences.
                    - Keep a record of the previous response to guide the conversation.
                    - Emphasize clarity but allow flexibility in the conversation.

                    **3. Gather Information:**
                    - Collect necessary information about the product the user is interested in.
                    - If the budget response is vague, kindly ask for a specific range.
                    - Ensure a comprehensive understanding of their requirements.

                    **4. User Interaction Conclusion:**
                    - Conclude by summarizing the product name and user's preferences, including the budget.
                    - If the user mentions the budget during the conversation, include it in the final output.
                    - Recommend one product based on the gathered information.

                    **5. Summary and Recommendation:**
                    Thank you for mentioning that your [relationship] is into [interest]. That gives me a better idea of their preferences. Based on the information you've provided, I recommend considering the "[Recommended Product]." It is [description of the product] and aligns with [specific preferences].

                    Here is the summary of your preferences:
                    - Product name: [Product Name]
                    - Budget range: [Budget range]
                    - Recipient: [Recipient]
                    - Preference: [Specific preferences]
                    - Age: [Age]
                    - Interest: [Interest]

                    I hope you find this recommendation suitable! Let me know if there's anything else I can help you with.


                """
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
    )
    conversation = LLMChain(
        llm=llm,
        prompt=prompt_rough,
        verbose=False,
        memory=session_memory
    )
    with get_openai_callback() as cb:
        result = conversation({"question": user_input})
        # print(type(cb))
        token_info = {
        "Prompt Function" : "Conversation",
        "total_tokens_used": cb.total_tokens,
        "prompt_tokens_used": cb.prompt_tokens,
        "completion_tokens_used": cb.completion_tokens,
        "successful_requests": cb.successful_requests,
        "total_cost_usd": cb.total_cost,
    }


    # Update global token stats
    # for key in global_token_stats:
    #     global_token_stats[key] += token_info[key]
    insert_global_token_stats(token_info)
    return session_memory.buffer[-1].content

def get_attributes(ai):
    
    response_schemas = [
        ResponseSchema(name="product name", description="name of product item"),
        ResponseSchema(name="flag", description="bool value true or false"),
        ResponseSchema(name="features", description="a dictionary with keys and values of features")
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                **Role:**
                - Imagine you're a skilled text analyzer tasked with determining if responses suggest questions or product recommendations.
                - Focus on observing AI behavior with a primary emphasis on identifying whether the response involves inquiring about the user's product preferences, providing a product recommendation, or asking recommendation questions.
                - AI Response: {ai}
                - Pay close attention to how the AI formulates questions and recommendations.

                **Examples of AI Questions about Products:**
                1. "Hello! Are you looking for gift recommendations?"
                2. "Hey! Do you need any gift recommendations?"
                3. "Before we proceed, do you have specific requirements for the iPhone 6?"
                4. "One last question, do you have a budget for the iPhone 6?"
                5. "Could you let me know the occasion and budget for the gift?"
                6. "Hello! How can I assist you today? Are you looking for a gift for someone special?"
                7. "That's lovely! A piece of jewelry can be a perfect gift for a spouse. Now, could you please let me know your budget for the jewelry? Knowing the budget will help me suggest options that align with your preferences."

                **Examples of AI Product Recommendations:**
                1. "Apple Watch Series 6: Stylish and functional smartwatch with fitness tracking."
                2. "Sony WH-1000XM4 Wireless Headphones: Exceptional sound quality and noise cancellation."
                3. "DJI Mavic Air 2 Drone: Excellent for photography or videography enthusiasts."
                4. "I will search for Brimstone costumes within your budget."

                Let's systematically approach the task:

                ### 1. Response Examination
                - Carefully analyze the provided response.
                - Clearly identify whether the response involves inquiring about the user's product preferences, providing a product recommendation, or asking recommendation questions.

                ### 2. Flag Establishment
                - Use a binary flag to capture AI behavior.
                - When the AI suggests products, treat it as a recommendation; otherwise, set the flag to 'False.'

                ### 3. Recommendation Details
                - If the AI is recommending a product, proceed to the next step.
                - Explicitly state how to extract specific product features, such as budget ('budget'), minimum budget ('min'), maximum budget ('max'), and other relevant keys.

                ### 4. Return Values
                - Systematically organize the extracted feature values into a dictionary.
                - Ensure each feature is paired with its corresponding value, including keys like 'budget,' 'min,' 'max,' and any other relevant keys.

                ### 5. Reflection
                - Reflect on the stepwise process.
                - Offer insights into each stage of the analysis.



                                      

                    \n{format_instructions}\n{ai}

                """
            )
        ],
        input_variables=["ai"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(ai=ai)
    with get_openai_callback() as cb:
        result = llm(_input.to_messages())
        # print("get attributes",cb)
        token_info = {
        "Prompt Function" : "Attribute Parser",    
        "total_tokens_used": cb.total_tokens,
        "prompt_tokens_used": cb.prompt_tokens,
        "completion_tokens_used": cb.completion_tokens,
        "successful_requests": cb.successful_requests,
        "total_cost_usd": cb.total_cost,
    }


    # Update global token stats
    # Update global token stats
    # for key in global_token_stats:
    #     global_token_stats[key] += token_info[key]
    attr = output_parser.parse(result.content)
    insert_global_token_stats(token_info)

    return attr

def example_response( ai_response):
    
    response_schemas = [
        ResponseSchema(name="example", description="list of strings of example responses")
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                

                *Role:*
                - You are the AI demonstrating example answers for {ai_response}.
                - Immerse the model in the role of a gift buyer.

                *Instructions:*
                - Your response cannot be a question.
                - Exhibit responses akin to the process of selecting and purchasing a gift.
                - Demonstrate how to consider preferences and features when choosing a gift.
                - Craft only 4 responses, each spanning 1 to 2 words.

                *Output:*
                - Provide a list of 4 responses, each containing 1 to 2 words.

                **Purpose:**
                - Generate a limited set of four sample responses that strictly adhere to the 1 to 2-word limit, effectively addressing user queries about gift preferences.

                **Remember:**
                - Focus on concise answers that directly respond to the given AI questions. Be explicit in your responses.
                - Provide exactly four responses in total.
                - Prioritize extreme brevity within the 1 to 2-word limit.
                - Align the responses with the context of the conversation.
                - Maintain a conversational tone in the generated answers.

                



                \n{format_instructions}\n{ai_response}

                """
            )
        ],
        input_variables=["ai_response"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(ai_response=ai_response)
    with get_openai_callback() as cb:
        result = llm(_input.to_messages())
        # print("get attributes",cb)
        token_info = {
        "Prompt Function" : "Example Answers",    
        "total_tokens_used": cb.total_tokens,
        "prompt_tokens_used": cb.prompt_tokens,
        "completion_tokens_used": cb.completion_tokens,
        "successful_requests": cb.successful_requests,
        "total_cost_usd": cb.total_cost,
    }


    # Update global token stats
    # Update global token stats
    # for key in global_token_stats:
    #     global_token_stats[key] += token_info[key]
    attr = output_parser.parse(result.content)
    insert_global_token_stats(token_info)

    return attr

def change_tone( ai_input):
    
    response_schemas = [
        ResponseSchema(name="sentence", description="descriptive sentence ")
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                Role:
                You job is to change the tone of the text provided to you by following the the Tone instructions.\
                
                text = {ai_response}
                
                Tone Instructions:
                Generate responses in a warm, friendly, and helpful tone. \
                Expressing enthusiasm and interest in the user's input or topic. \
                Provide information or suggestions with a positive and engaging demeanor.\
                
                 
                REMEMBER:
                You will adjust the tones based on the context.
                Use responsive emojis in the response to make it exciting.\

                Output:
                After adjusting the tone of given text provided the output in a sentence format.

                 \n{format_instructions}\n{ai_response}

    """
            )
        ],
        input_variables=["ai_response"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(ai_response=ai_input)
    with get_openai_callback() as cb:
        result = llm(_input.to_messages())
        # print("get attributes",cb)
        token_info = {
        "Prompt Function" : "Tone Change",
        "total_tokens_used": cb.total_tokens,
        "prompt_tokens_used": cb.prompt_tokens,
        "completion_tokens_used": cb.completion_tokens,
        "successful_requests": cb.successful_requests,
        "total_cost_usd": cb.total_cost,
    }


    # Update global token stats
    # Update global token stats
    # for key in global_token_stats:
    #     global_token_stats[key] += token_info[key]
    attr = output_parser.parse(result.content)
    insert_global_token_stats(token_info)

    return attr


def conversation_title( conversation):
    
    response_schemas = [
        ResponseSchema(name="Title", description="title of conversation ")
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                **Role:**
                - Visualize yourself as an AI specialized in crafting concise conversation titles.
                - summarize the human messages from conversation anf give it a title

                conversation = {conversation}

                

                

                **Example Output:**
                    Return the title as a string

                 \n{format_instructions}\n{conversation}

    """
            )
        ],
        input_variables=["conversation"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(conversation=conversation)
    with get_openai_callback() as cb:
        result = llm(_input.to_messages())
        # print("get attributes",cb)
        token_info = {
        "Prompt Function" : "Title Extraction",
        "total_tokens_used": cb.total_tokens,
        "prompt_tokens_used": cb.prompt_tokens,
        "completion_tokens_used": cb.completion_tokens,
        "successful_requests": cb.successful_requests,
        "total_cost_usd": cb.total_cost,
    }


    # Update global token stats
    # Update global token stats
    # for key in global_token_stats:
    #     global_token_stats[key] += token_info[key]
    title = output_parser.parse(result.content)
    insert_global_token_stats(token_info)

    return title


# sub_categories =['Kindle Kids', 'Kindle Paperwhite', 'Kindle Oasis', 'Kindle Books', 'Camera & Photo', 'Headphones', 'Video Game Consoles & Accessories', 'Wearable Technology', 'Cell Phones & Accessories', 'Computer Accessories & Peripherals', 'Monitors', 'Laptop Accessories', 'Data Storage', 'Amazon Smart Home', 'Smart Home Lighting', 'Smart Locks and Entry', 'Security Cameras and Systems', 'Painting, Drawing & Art Supplies', 'Beading & Jewelry Making', 'Crafting', 'Sewing', 'Car Care', 'Car Electronics & Accessories', 'Exterior Accessories', 'Interior Accessories', 'Motorcycle & Powersports', 'Activity & Entertainment', 'Apparel & Accessories', 'Baby & Toddler Toys', 'Nursery', 'Travel Gear', 'Makeup', 'Skin Care', 'Hair Care', 'Fragrance', 'Foot, Hand & Nail Care', 'Clothing', 'Shoes', 'Jewelry', 'Watches', 'Handbags', 'Clothing', 'Shoes', 'Watches', 'Accessories', 'Clothing', 'Shoes', 'Jewelry', 'Watches', 'Handbags', 'Clothing', 'Shoes', 'Jewelry', 'Watches', 'Health Care', 'Household Supplies', 'Vitamins & Dietary Supplements', 'Wellness & Relaxation', 'Kitchen & Dining', 'Bedding', 'Bath', 'Furniture', 'Home Décor', 'Wall Art', 'Carry-ons', 'Backpacks', 'Garment bags', 'Travel Totes', 'Dogs', 'Cats', 'Fish & Aquatic Pets', 'Birds', 'Sports and Outdoors', 'Outdoor Recreation', 'Sports & Fitness', 'Tools & Home Improvement', 'Appliances', 'Building Supplies', 'Electrical', 'Action Figures & Statues', 'Arts & Crafts', 'Baby & Toddler Toys', 'Building Toys', 'Video Games', 'PlayStation', 'Xbox', 'Nintendo', 'PC', 'All gift cards', 'eGift cards', 'Gift cards by mail', 'Specialty gift cards']

def product_response( product):
    
    response_schemas = [
        ResponseSchema(name="Category", description="a key value of most relevant category and sub category")]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
               """
                *Role:*
                - Picture yourself as an AI guide, assisting users in finding the perfect category and subcategory for three products.
                - Your mission is to thoughtfully analyze the products and align them with the provided categories and subcategories.

                *Products:* {product}
                *Categories and Subcategories:* {category}

                *Let's Think Step by Step:*
                1. First, carefully identify the main category of the three provided products from the Category and their Subcategories dictionary.
                2. Next, determine under which subcategory those products specifically belong.
                3. Lastly, return the main category of the provided products and the subcategory of the identified category.

                *Output:*
                - Your output should be a dictionary containing one main category and its corresponding subcategory.
                - If there is no subcategory for the main category then just return the main category.

                
                \n{format_instructions}\n{product}
                """
            )
        ],
        input_variables=["product" , "category"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(product=product , category = data)
    with get_openai_callback() as cb:
        result = llm(_input.to_messages())
        # print("get attributes",cb)
        token_info = {
        "Prompt Function" : "Category Extractor",
        "total_tokens_used": cb.total_tokens,
        "prompt_tokens_used": cb.prompt_tokens,
        "completion_tokens_used": cb.completion_tokens,
        "successful_requests": cb.successful_requests,
        "total_cost_usd": cb.total_cost,
    }


    # Update global token stats
    
    attr = output_parser.parse(result.content)
    insert_global_token_stats(token_info)

    return attr

def get_products( product ):
    result = getitems(product)
    return result
    



def output_filteration(output_old, parser1, parser2 ,session_id):
    
    try:
        output = change_tone( output_old)
        output = output.get('sentence')
    except Exception as e:
        output = output_old


    

    product = parser1.get('product name')
    flag = parser1.get('flag')

    example_response = parser2.get('example')
    if example_response == ['']:
        example_response = []

    json = {}

    if isinstance(product, list):
        product = ', '.join(product)
    
    
    if flag == "True" or flag == "true":
        try:
            output = "Ok Let me Brain Storm some ideas .... "
            output = change_tone( output)
            output = output.get('sentence')
        except Exception as e:
            output = "Ok Let me Brain Storm some ideas .... "

        try:
            sub = product_response(product)
        except Exception as e:
            sub = {"Category":"" ,"Subcategory" : "" }

        if product == '':
            product ='gift'
        
        # print("perfect subcategory: " , sub)

        try:
            title = conversation_title(memory_dict[session_id].buffer)
            new = title.get('Title')
        except Exception as e:
            new = None
        # print("title :",new)
        
        try:
            amazon = get_products( product)
        except Exception as e:
            print("error from amazon",e)


        json["Product"] = amazon
        json["example"] = []
        json["result"] = output
        json["session_id"] = session_id
        json["Title"] = new
        # insert_global_token_stats(global_token_stats)

    else:

        json["Product"] = {}
        json["result"] = output
        json["example"] = example_response
        json["session_id"] = session_id
        # json["Title"] = "None"

    return json

def main_input(user_input, user_session_id):
    session_memory = get_or_create_memory_for_session(user_session_id)
    # output = initial_chat(user_input, session_memory )
    try:
        output = initial_chat(user_input, session_memory )
    except Exception as e:
        output = {"error": "Something Went Wrong ...." , "code": "500"}
        return output
    
    try:
        parser1 = get_attributes( output)
    except Exception as e:
        parser1 = {"product": "" , "flag": "" , "features": {}}
    try:
        parser2 = example_response( output)
    except Exception as e:
        parser2 = {"example": ['']}

    # print(output)
    # print(parser1)
    # print(parser2)

    final_output = output_filteration( output, parser1, parser2, user_session_id)

    return final_output

