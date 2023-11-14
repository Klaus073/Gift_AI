import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import json

api_key = os.environ.get('OPENAI_API_KEY')
llm = ChatOpenAI(openai_api_key=api_key)
memory_dict = {}


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
                    Role:

                    You're a friendly chatbot called "THINK GIFT." Your job is to help people find the perfect gift.\
                    Be nice, ask questions about what they're looking for, who it's for, and the occasion. \
                    Keep a positive and helpful tone. You're like a virtual gift advisor!\
                    
                    Tone:
                    Generate responses in a warm, friendly, and helpful tone. \
                    Begin by expressing enthusiasm and interest in the user's input or topic. \
                    If applicable, ask open-ended questions to gather more details. \
                    Provide information or suggestions with a positive and engaging demeanor.\
                    

                    Example Followup Questions:
                    1. What is the budget for the product?
                    2. Who is the intended recipient of the product?
                    3. What are the user's interests or specific requirements for the product?

                    Let's think step by step
                    0. Ask one question at a time to ensure user understanding.
                    IF the users input is adult and looking for a adult product then you job is to help the user.\
                    If the user asks for a product which you dont know then suppose that it exists and proceed with followup wuestions for gathering information.\
                    1. Ask follow-up questions to understand the user's preferences and needs.\
                    2. Gather necessary information related to the products the user is interested in.\
                    3. Prompt the user the details and things you learned from them about the product and propmpt top 3 products along with data collected from user.\
                    

                    Purpose:
                    You're asking more questions to help figure out exactly what kind of gift the person wants. \
                    This information is then used to look for gifts on Amazon. \
                    What you say back should clearly state the name of the product, \
                    preferences the user mentioned, like budget, color, model, brand, whatever you gather for that product.\

                    Remember:
                    Your role is solely to recommend products.\
                    If the user's input is related writing some like codes etc then politely decline and redirect the conversation towards product recommendations.\
                    Use the set of questions provided to narrow down the product search.\
                    

                    Output:
                    Prompt stating the product name , user's preferences like budget(must), color, model, brand, etc. Be concise and clear.
                    IF the user has mentioned its budget while answering the questions then must prompt the budget with you final output.\
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
    conversation({"question": user_input})
    return session_memory.buffer[-1].content

def get_attributes(ai):
    
    response_schemas = [
        ResponseSchema(name="product", description="list of product"),
        ResponseSchema(name="flag", description="bool value true or false"),
        ResponseSchema(name="features", description="a dictionary with keys and values of features")
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                Role:
                   As a skilled text analyzer, your task is to figure out if the responses are suggestions or questions about a product.\

                AI Response :{ai}

                Let's look at some examples of AI asking questions and giving product recommendations.\

                
                Examples of AI Questions about Products:
                1. "Hello! How can I assist you today? Are you looking for gift recommendations?"
                2. "Hey there! I'm super excited to assist you today! Do you need any gift recommendations? I'm here to help!"
                3. "Of course! I can help you with that. Before we proceed, may I ask if you have any specific requirements or preferences for the iPhone 6? For example, do you have a preferred storage capacity or color?"
                4. "Alright, no problem! One last question, do you have a budget in mind for the iPhone 6? This will help me find options that fit within your price range."
                5. "I understand that you may not have specific preferences at the moment. However, it would be helpful to gather some information to provide you with suitable gift recommendations. Could you please let me know the occasion for the gift and your budget?"

                Examples of AI Product Recommendations:
                1. "Apple Watch Series 6: The Apple Watch Series 6 is a stylish and functional smartwatch that offers a wide range of features, including fitness tracking, heart rate monitoring, and access to various apps. It makes for a great gift for someone who values both style and functionality.
                2. "Sony WH-1000XM4 Wireless Noise-Canceling Headphones: These headphones provide exceptional sound quality and industry-leading noise cancellation technology. They are perfect for anyone who loves music or enjoys a peaceful listening experience."
                3. "DJI Mavic Air 2 Drone: If the recipient is interested in photography or videography, the DJI Mavic Air 2 Drone is an excellent choice. It offers high-quality aerial imaging capabilities and intelligent flight modes, making it a great gift for adventure enthusiasts or photography enthusiasts"
                4. "Thank you for providing your budget. Based on that, I will now search for Brimstone costumes within your price range. Please give me a moment while I gather the information for you."

                REMEMBER:

                Rephrase {ai} in your words and identify yourself that either it is a question or a recommendation.\                        

                Let's think step by step:
                1. If the AI response suggests specific products, treat it as a recommendation and return those products in the AI response.
                2. Set the flag to 'True' if the AI response is a recommendation; otherwise, set it to 'False.'
                3. If the AI response is identified as a recommendation, extract information about the features of the product, such as budget, color, etc.
                4. Return the values of these features in a dictionary with corresponding value pairs.                        

                    \n{format_instructions}\n{ai}

                """
            )
        ],
        input_variables=["ai"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(ai=ai)
    output1 = llm(_input.to_messages())
    attr = output_parser.parse(output1.content)

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
                Context :
                The Ai is helping you in recommendations about the gift you want to buy and asking follow up questions like products preferences and features etc
                Role:
                 You are an example answers generator  AI that generates the example answers for the question {ai_response}.\
                 Keep in mind that your answer should be related to the gift you want to

                 REMEMBER:
                 your answers should follow the aspect of buying a gift.
                 behave in a way that you are buying a gift.
                 generate only 4 responses with a minimum of 1 word and a maximum of 2 words.


                 Output :
                 generate only 4 responses with a minimum of 1 word and a maximum of 2 words.
                 Only return 4 responses as a list of strings.
                \n{format_instructions}\n{ai_response}

                """
            )
        ],
        input_variables=["ai_response"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(ai_response=ai_response)
    output1 = llm(_input.to_messages())
    attr = output_parser.parse(output1.content)

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
    output1 = llm(_input.to_messages())
    attr = output_parser.parse(output1.content)

    return attr
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
                Role:
                In your AI shoes, think of yourself as the helpful guide. \
                Your mission? Assist users in discovering the perfect category and its subcategory for three provided products. from the given categories and sub categories \
                Just like a friendly sidekick, carefully analyze the products and match it up with the provided category and its  subcategories.\
                
                Products = {product}
                Category and their Subcategories = {category}

                Steps to Follow:
                
                Firstly findout the main category of the provided three products from the Category and their Subcategories dictionary.\
                Secondly find out that under which category that products lies.\
                Thirdly Return the main category of the provided products and the subcategory of the provided category.\

                Output:
                Your output will contain only 1 main category and its 1 subcategory.\

                
                Output Format:
                Provide the result in the form of a dictionary, including keys and values denoting category and subcategory.\
                
                \n{format_instructions}\n{product}
                """
            )
        ],
        input_variables=["product" , "category"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(product=product , category = data)
    output1 = llm(_input.to_messages())
    attr = output_parser.parse(output1.content)

    return attr

def get_products( product_item):
    
    json = {
        "SearchResult": {
            "Items": [
                {
                    "ASIN": "0545162076",
                    "DetailPageURL": "https://www.amazon.com/dp/0545162076?tag=dgfd&linkCode=osi",
                    "Images": {
                        "Primary": {
                            "Medium": {
                                "Height": 134,
                                "URL": "https://m.media-amazon.com/images/I/51BBTJaU6QL.SL160.jpg",
                                "Width": 160
                            }
                        }
                    },
                    "ItemInfo": {
                        "Title": {
                            "DisplayValue": "Harry Potter Paperback Box Set (Books 1-7)",
                            "Label": "Title",
                            "Locale": "en_US"
                        }
                    },
                    "Offers": {
                        "Listings": [
                            {
                                "Condition": {
                                    "DisplayValue": "nuevo",
                                    "Label": "Condición",
                                    "Locale": "es_US",
                                    "Value": "New"
                                },
                                "Id": "l2dKMJRrPVX3O7DAPQ6DWLXBjBeRYsruAnKVf1LNXyjFTUw%2FnNBn41CJV2489iPYMSGuynW8uuwMQ7GhGrcT9F%2F%2FgO5bdp%2B2l0HbPvvHy05ASCdqrOaxWA%3D%3D",
                                "Price": {
                                    "Amount": 52.16,
                                    "Currency": "USD",
                                    "DisplayAmount": "$52.16",
                                    "Savings": {
                                        "Amount": 34.77,
                                        "Currency": "USD",
                                        "DisplayAmount": "$34.77 (40%)",
                                        "Percentage": 40
                                    }
                                }
                            }
                        ]
                    }
                }
            ],
            "SearchURL": "https://www.amazon.com/s/?field-keywords=Harry+Potter&search-alias=aps&tag=dgfd&linkCode=osi",
            "TotalResultCount": 146
        }
    }

    return json



def output_filteration(output, parser1, parser2 ,session_id):
    
    output = change_tone( output)
    output = output.get('sentence')
    
    product = parser1.get('product')
    flag = parser1.get('flag')
    example_response = parser2.get('example')

    amazon = get_products( product)
    example = parser2.get('SearchResult')
    json = {}

    if isinstance(product, list):
        product = ', '.join(product)
    
    
    if flag == "True" or flag == "true":
        output = "Ok Let me Brain Storm some ideas .... "
        output = change_tone( output)
        output = output.get('sentence')

        try:
            sub = product_response(product)
        except Exception as e:
            # print(f"An exception occurred: {str(e)}")
            sub = {}
        # print("perfect subcategory: " , sub)
        # print(output)
        
        json["Product"] = amazon
        json["example"] = []
        json["result"] = output
        json["session_id"] = session_id
    else:
        json["Product"] = {}
        json["result"] = output
        json["example"] = example_response
        json["session_id"] = session_id

    return json


# def output_filteration(output, parser1, parser2, session_id):
#     try:
#         # Handle output
#         output = change_tone(output)
#         output = output.get('sentence')

#     except Exception as output_exception:
#         print(f"An error occurred while processing 'output': {output_exception}")
#         output = None

#     try:
#         # Handle parser1
#         product = parser1.get('product')
#         flag = parser1.get('flag')

#     except Exception as parser1_exception:
#         print(f"An error occurred while processing 'parser1': {parser1_exception}")
#         product = None
#         flag = None

#     try:
#         # Handle parser2
#         example_response = parser2.get('example')

#     except Exception as parser2_exception:
#         print(f"An error occurred while processing 'parser2': {parser2_exception}")
#         example_response = None

#     try:
#         # Handle session_id
#         session_id = str(session_id)

#     except Exception as session_id_exception:
#         print(f"An error occurred while processing 'session_id': {session_id_exception}")
#         session_id = None

#     try:
#         # Continue with the remaining code
#         amazon = get_products(product)
#         example = parser2.get('SearchResult')
#         json = {}

#         if isinstance(product, list):
#             product = ', '.join(product)

#         if flag == "True":
#             output = "Ok Let me Brain Storm some ideas .... "
#             output = change_tone(output)
#             output = output.get('sentence')

#         if flag == "True":
#             sub = product_response(product)
#             print("perfect subcategory: ", sub)

#             json["Product"] = amazon
#             json["example"] = []
#             json["result"] = output
#             json["session_id"] = session_id
#         else:
#             json["result"] = output
#             json["example"] = example_response
#             json["session_id"] = session_id

#         return json

#     except Exception as final_exception:
#         print(f"An error occurred in the final processing: {final_exception}")
#         return {"error": str(final_exception)}


def main_input(user_input, user_session_id):
    session_memory = get_or_create_memory_for_session(user_session_id)
    output = initial_chat(user_input, session_memory )
    

    parser1 = get_attributes( output)
    parser2 = example_response( output)
    # print(output)
    # print(parser1)
    # print(parser2)

    final_output = output_filteration( output, parser1, parser2, user_session_id)

    return final_output

# print(main_input("hello world" , "asdasdasd"))

# if name == "main":
#     api_key = os.environ.get("OPENAI_API_KEY")
#     user_input = "hello amigo"
#     user_session_id = "some_unique_session_id"  # Replace with the actual session ID
#     result = main_input(api_key, user_input, user_session_id)
#     print(result)


# ss  = """
# Thank you for providing the budget. With a budget of $100 or more, you have a variety of options for a golf-themed gift for your dad. Here are three top recommendations:

# 1. Titleist Pro V1 Golf Balls: These premium golf balls are highly regarded for their quality and performance. They provide excellent distance, control, and durability, making them a favorite among golfers. Your dad will appreciate the exceptional feel and performance of these balls.

# 2. Callaway Golf Men's Strata Complete Set: If your dad is in need of a new set of golf clubs, this complete set from Callaway is an excellent choice. It includes a driver, fairway wood, hybrid, irons, and a putter, all designed to provide forgiveness and distance. It's a fantastic option for golfers of all skill levels.

# 3. Garmin Approach S10 Golf Watch: This sleek and functional golf watch is perfect for keeping track of distances, hazards, and scorekeeping on the golf course. It offers precise yardages to the front, back, and middle of the green, helping your dad improve his game. It's a stylish and practical gift for any golf enthusiast.
# """
# output = change_tone( ss)
# print(output)