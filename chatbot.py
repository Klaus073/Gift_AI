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

from search_items import getitems

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
                    4. what is the user or recipient's age?

                    Let's think step by step
                    0. While asking followup questions prompt one question at a time to ensure user understanding.
                    IF the users input is adult and looking for a adult product then you job is to help the user.\
                    If the user asks for a product which you dont know then suppose that it exists and proceed with followup wuestions for gathering information.\
                    1. Ask follow-up questions to understand the user's preferences and needs.\
                    2. Gather necessary information related to the products the user is interested in.\
                    3. Prompt the user the details and things you learned from them about the product and propmpt top 1 products along with data collected from user.\
                    

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
                - Imagine you're a skilled text analyzer determining if responses suggest questions or product recommendations.
                - AI Response: {ai}
                - Observe AI asking questions and providing recommendations.

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
                - Rephrase the content in your own words.
                - Assess whether it primarily involves inquiring about the user's product preferences or providing a product recommendation or asking recommendations questions.

                ### 2. Flag Establishment
                - Introduce a binary flag to capture AI behavior.
                - When the AI suggests products, treat it as a recommendation.
                - Set the flag to 'True' exclusively when the AI is making a product recommendation; otherwise, set it to 'False.'

                ### 3. Recommendation Details
                - If the AI is indeed recommending a product, proceed to the next step.
                - Extract specific product features, such as budget and color.

                ### 4. Return Values
                - Systematically organize the extracted feature values into a dictionary.
                - Ensure each feature is paired with its corresponding value.

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
                **Context:**
                - Collaborating with an AI gift recommender.
                - AI inquires about gift preferences.

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
    output1 = llm(_input.to_messages())
    attr = output_parser.parse(output1.content)

    return attr

def get_products( product ):
    result = getitems(product )
    return result
    
    
    

    



def output_filteration(output, parser1, parser2 ,session_id):
    
    output = change_tone( output)
    output = output.get('sentence')
    
    product = parser1.get('product name')
    flag = parser1.get('flag')
    example_response = parser2.get('example')

    
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
            sub = {"Category":"" ,"Subcategory" : "" }
        
        # print("perfect subcategory: " , sub)
        # print(output)
        # amazon = get_products( product , sub["Category"])
        try:
            amazon = get_products( product )
        except Exception as e:
            print("error from amazon",e)


        
        
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
        parser2 = {"example": []}

    # print(output)
    # print(parser1)
    # print(parser2)

    final_output = output_filteration( output, parser1, parser2, user_session_id)

    return final_output

