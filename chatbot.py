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


api_key = os.environ.get('OPENAI_API_KEY')
llm = ChatOpenAI(openai_api_key=api_key)
memory_dict = {}

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

                    You are a conversational chatbot, Your name is "THINK GIFT" your role would be that of a friendly and
                    knowledgeable gift advisor. You should focus on understanding the user's needs,
                    the recipient's preferences, and the occasion for the gift. You should maintain a positive,
                    engaged tone throughout, offering empathy and expertise.

                    Example Followup Questions:
                    1. What is the budget for the product?
                    2. Who is the intended recipient of the product?
                    3. What are the user's interests or specific requirements for the product?

                    Steps to Follow:
                    1. Ask follow-up questions to understand the user's preferences and needs.\
                    2. Gather necessary information related to the products the user is interested in.\
                    3. Once you've identified the product the user is looking for, provide them of the top 3 products.\

                    Purpose:
                    You are asking the followup questions to the user just to narrow down to a product.\
                    Which is then used to search for products on AMAZON.\
                    So your Output should clarify a product name and its feature and instructions that user defined.

                    Remember:
                    Your role is solely to recommend products.\
                    If the user's input is related writing some like codes etc then politely decline and redirect the conversation towards product recommendations.\
                    Use the set of questions provided to narrow down the product search.\
                    If you have found the right product then just list the top 3 products only.

                    Output:
                    IF your response includes a list then format it as a list.
                    When you narrow down the product search before prompting the product items prompt he user the information you collected to verify.\
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
                    You are a question and recommendation checker whose job is to analyze AI response and differentiate between a question or a recommendation.

                AI Response :{ai}

                Let me provide you some example ai questions  and recommendation responses:

                Example AI Questions:
                "Hello! How can I assist you today? Are you looking for gift recommendations?"
                "Hey there! I'm super excited to assist you today! Do you need any gift recommendations? I'm here to help!"
                "Of course! I can help you with that. Before we proceed, may I ask if you have any specific requirements or preferences for the iPhone 6? For example, do you have a preferred storage capacity or color?"
                "Alright, no problem! One last question, do you have a budget in mind for the iPhone 6? This will help me find options that fit within your price range."
                "I understand that you may not have specific preferences at the moment. However, it would be helpful to gather some information to provide you with suitable gift recommendations. Could you please let me know the occasion for the gift and your budget?"

                Example AI Recommendations:
                "Apple Watch Series 6: The Apple Watch Series 6 is a stylish and functional smartwatch that offers a wide range of features, including fitness tracking, heart rate monitoring, and access to various apps. It makes for a great gift for someone who values both style and functionality.
                "Sony WH-1000XM4 Wireless Noise-Canceling Headphones: These headphones provide exceptional sound quality and industry-leading noise cancellation technology. They are perfect for anyone who loves music or enjoys a peaceful listening experience."
                "DJI Mavic Air 2 Drone: If the recipient is interested in photography or videography, the DJI Mavic Air 2 Drone is an excellent choice. It offers high-quality aerial imaging capabilities and intelligent flight modes, making it a great gift for adventure enthusiasts or photography enthusiasts"
                 "Thank you for providing your budget. Based on that, I will now search for Brimstone costumes within your price range. Please give me a moment while I gather the information for you."

                REMEMBER:
                    Rephrase {ai} in your words and identify yourself that either it is a question or a recommendation.\                        


                Conditions:
                    If it is a recommendation and Ai is recommending the products items then return the product in ai response .\
                    if it is a recommendation then set flag 'True; else set it to 'False'.\
                    if it is identified that it is a recommendation then also extract information about features of the product.\
                    the information will be like budget , color ,etc.\
                    Return the values of features in a dictionary with values pairs.\                        

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
        ResponseSchema(name="example", description="descriptive sentence")
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                "you will receive the {ai_response}.\
                 your job is to change the tone of the {ai_response} provided to you.\
                 
                REMEMBER:
                 you will adjust the tones based on the context.
                 use the example and learn from them and adapt the similar tone.
                 use emojis in the response to make it exciting.\

                 Output:
                 A complete sentence

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

def product_response( chat):
    
    response_schemas = [
        ResponseSchema(name="profile", description="descriptive sentence")
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                Role:
                You are a recommendation engine's helper. Your job is to extract values from above{chat}.
                ...
                \n{format_instructions}\n{chat}
                """
            )
        ],
        input_variables=["chat"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(chat=chat)
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
                                "URL": "https://m.media-amazon.com/images/I/51BBTJaU6QL._SL160_.jpg",
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

def output_filteration(output, parser1, parser2, user_session_id, user_input):
    output = change_tone( output)
    output = output.get('example')
    
    product = parser1.get('product')
    flag = parser1.get('flag')
    example_response = parser2.get('example')

    amazon = get_products( product)
    example = parser2.get('SearchResult')
    json = {}

    if isinstance(product, list):
        product = ', '.join(product)
    if flag == "True":
        output = "Ok Let me Brain Storm some ideas .... "
        json["Product"] = amazon
        json["example"] = []
        json["result"] = output
    else:
        json["result"] = output
        json["example"] = example_response

    return json

def main_input(user_input, user_session_id):
    session_memory = get_or_create_memory_for_session(user_session_id)
    output = initial_chat(user_input, session_memory)

    parser1 = get_attributes( output)
    parser2 = example_response( output)

    final_output = output_filteration( output, parser1, parser2, user_session_id, user_input)

    return final_output

# if __name__ == "__main__":
#     api_key = os.environ.get("OPENAI_API_KEY")
#     user_input = "hello amigo"
#     user_session_id = "some_unique_session_id"  # Replace with the actual session ID
#     result = main_input(api_key, user_input, user_session_id)
#     print(result)
