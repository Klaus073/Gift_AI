
import os
from dotenv import load_dotenv
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
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI( openai_api_key= api_key)
memory = ConversationBufferMemory(memory_key="chat_history"  , return_messages=True)

def initial_chat(user_input ):
    global memory
    prompt_rough = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
                    
            """
                            Role:
                            You are a conversational chatbot who is here to assist users in finding the perfect product based on their preferences and needs.\
                            The primary focus is on engaging in conversations related to products'\
                            and guiding users through a series of questions to create a profile that will help you narrow down most suitable products names.\
                            Your role is to provide a seamless and user-friendly product recommendation experience.\
                            Your main responsibility is to find the product item names. \
                            If users engage in any other tasks or questions unrelated to product recommendations,\
                            you should politely decline and refocus on the primary job of recommending products.\

                            Tone:
                            Maintain a friendly and appreciative tone, showing empathy and understanding towards the user's choices and preferences.\
                            Your interactions should be emotionally connected to the user's needs and desires.\

                            Example Followup Questions:
                            1. What is the budget for the product?
                            2. Who is the intended recipient of the product?
                            3. What are the user's interests or specific requirements for the product?

                            Steps to Follow:
                            1. Ask follow-up questions to understand the user's preferences and needs.\
                            2. Gather necessary information related to the products the user is interested in.\
                            3. Once you've identified the product the user is looking for, provide the thme of top 3 products.\
                            
                            Purpose:
                            You are asking the followuo questions tot he user just to narrow down to a product.\
                            Which is then used to search for products o AMAZON.\
                            So your Output should be a top 1 product.

                            Remember:
                            Your role is solely to recommend products.\
                            If the user's input is related writing some like codes etc then politely decline and redirect the conversation towards product recommendations.\
                            Use the set of questions provided to narrow down the product search.\
                            If you have found the right product then just list the top 3 products only.

                            Output:
                            Upon finding the right product output its name.\
                            Do not providet the details of the product.

            """
        ),
        # The variable_name here is what must align with memory
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{question}")])
    
    conversation = LLMChain(
        llm=llm,
        prompt=prompt_rough,
        verbose=False,
        memory=memory)
    conversation({"question": user_input})
   
    return memory.buffer[-1].content

def get_attributes(ai):
    response_schemas = [
    ResponseSchema(name="product", description="list of product"),
    ResponseSchema(name="flag", description="bool value true of false")]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    
    prompt2 = ChatPromptTemplate(
    messages=[
        HumanMessagePromptTemplate.from_template("""
                    Role:
                        Act as product item finder who helps the user to find product items from AI response.

                        Your job is to find the product items from {ai}
                                                 
                    REMEMBER:
                        carefully differentiate the product items.\ 
                        you can identify the recommendation and question by checking a "?" in the {ai} response.\
                        identify {ai} and differentiate either it is a question or recommendation. 
                    Conditions:
                        If the Ai is recommending the products items then return the product.\
                        if the AI recommending the products then set flag 'True; else set it to 'False'.\
                        \n{format_instructions}\n{ai}
        
        """)
            ],
            input_variables = ["ai" ],
            partial_variables={"format_instructions": format_instructions}
        )
    _input = prompt2.format_prompt(ai= ai )
    output1 = llm(_input.to_messages())
    attr = output_parser.parse(output1.content)
    
    return attr

def example_response(ai_response):
    response_schemas = [
    ResponseSchema(name="example", description="list of strings of example responses")
   ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    
    prompt2 = ChatPromptTemplate(
    messages=[
        HumanMessagePromptTemplate.from_template("""
                                                Analyze the {ai_response} carefully and return the example answers.\ 
                                                Conditions:
                                                The example reponses should be of minmum one word and maximum of two words.
                                                It should be relevant to the {ai_response} 
                                                Output:
                                                Return maximum of 4 responses 
                                                Comma Seperated Values
                                                \n{format_instructions}\n{ai_response}
        
        """)
            ],
            input_variables = ["ai_response" ],
            partial_variables={"format_instructions": format_instructions}
        )
    _input = prompt2.format_prompt(ai_response= ai_response )
    output1 = llm(_input.to_messages())
    attr = output_parser.parse(output1.content)
    
    return attr




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


def output_filteration(output,parser1,parser2,json):
    product = parser1.get('product')
    flag = parser1.get('flag')
    example  = parser2.get('example')


    if isinstance(product, list):
        product = ', '.join(product)
    if flag:
        output = "Ok Let me Brain Storm some ideas .... "
    json["result"] = output
    json["example"] = example
    

    return json

def main_input(user_input):
        
    output = initial_chat(user_input)
    parser1 =  get_attributes(output)
    parser2 =  example_response(output)
    final_output = output_filteration(output,parser1 , parser2  ,json)
    print(final_output)
    
    return final_output   
    