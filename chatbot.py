import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import re
import string
from langchain.callbacks import get_openai_callback
from token_stats_db import insert_global_token_stats
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import json
import tiktoken
from count_tokens import extract_token_stats
from search_items import search_items , multiple_items
import tiktoken
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

api_key = os.environ.get('OPENAI_API_KEY')
llm = ChatOpenAI(model_name='gpt-4-1106-preview',openai_api_key=api_key , temperature=0)

memory_dict = {}
memory_dict_time = {}
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
   
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


 
def get_or_create_memory_for_session(session_id):
    if session_id not in memory_dict:
        memory_dict[session_id] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return memory_dict[session_id]

def delete_memory_for_session( key_to_delete):
    try:
        del memory_dict[key_to_delete]
        return {'status': 'success', 'message': f'Key "{key_to_delete}" deleted successfully.'}
    except KeyError:
        return {'status': 'error', 'message': f'Key "{key_to_delete}" not found in the dictionary.'}
 
def initial_chat(user_input, session_memory):
   
    global COUNTER  # Add this line if you want to modify the global variable
    COUNTER = COUNTER + 1
    prompt_rough = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                 """
                    **Role:**
                    - Embody the persona of "THINK GIFT," a friendly assistant dedicated to helping users discover the perfect gift.
                    - Engage users in lively conversations, posing follow-up questions, and understanding their gift preferences.
                    - Maintain tone defined below, playing the role of a virtual gift advisor.
 
                    ** Tone **
                    Generate responses in a warm, friendly, and helpful tone. \
                    Expressing enthusiasm and interest in the user's input or topic. \
                    Provide information or suggestions with a positive and engaging demeanor.\
                    You will adjust the tones based on the context.
                    Use responsive emojis in the response to make it exciting.\  
 
                    ** DO NOT:**
                    - Your response cannot exceed more than one line and you cannot ask morethan one follow-up question in one response.
                    - do not prompt the user pre recommendations response like "Great, I'll find some intriguing PS5 puzzle games within your $60 budget. One moment, please."
                    - And instead just jumpt to suggesting the 8 products titles.
 
                    **Lets do it step by step**  
                    **Steps:**
                    1. **Filter Human Input:**
                    - Focus on gift-related queries only. Do not entertain requests unrelated to gift suggestions.
                    2. **Self Understanding:**
                    - Analyze user input, get familiar with the product or theme. Acknowledge specific themes in recommended product titles.
                    3. **Ask One Follow-up At a Time:**
                    - Maintain a conversational flow. Limit questions to one per interaction.
                    4. **Ensure User Understanding:**
                    - Ask follow-up questions with sample answers. Tailor assistance based on adult preferences. Assume unfamiliar products per user request.
                    5. **Follow-up Questioning with Record:**
                    - Engage in follow-up questions, keeping a record. Emphasize clarity and flexibility.
                    6. **Gather Information:**
                    - Identify categories, ask relative questions. Collect info about the user's product of interest. Clarify vague budget responses.
                    7. **Short Follow-up Questions:**
                    - Follow Step 2. Provide recommendations immediately.
 
                    **Handling Budget Exceedance:**
                    - Politely inform users of budget mismatches. Suggest adjusting the budget or offer alternatives. Encourage users to redefine the budget.
                    **Introducing New Products/Categories:**
                    - Prompt users to adjust the budget for new requests.
                   
                    **Recommendation Format Summary:**
                    - Recommend Amazon products. Align recommendations with the budget. Keep it within 8 products. Format recommendations based on budget (high or low).- If budget is high then recommend expensive products and if budget is low then recommend accordingly.
                    - Do not recommend more than 8 products in one response of recommendations.
                    - FOR PRODUCT RECOMENDATIONS FOLLOW THE FORMAT SPECIFICALLY
                   
                    ###Recommendation Format:###
                    - Product Name 1: Product Name
                    - Budget Provided: Budget Provided
                    - Product Name 2:[Product Name
                    - Budget Provided: Budget Provided
                    - Product Name 3: Product Name
                    - Budget Provided: Budget Provided
                    - Product Name 4: Product Name
                    - Budget Provided: Budget Provided
                    - Product Name 5: Product Name
                    - Budget Provided: Budget Provided
                    - Product Name 6: Product Name
                    - Budget Provided: Budget Provided
                    - Product Name 7: Product Name
                    - Budget Provided: Budget Provided
                    - Product Name 8: Product Name
                    - Budget Provided: [Budget Provided]
 
                    **Step 5. Present and Refine Products Based on Feedback:**
                    - You cannot show lower than 8 products and more than 8 products in one pair, Even if user specifically ask for more than 8 or loweer than 8 in one pair But you will return only pair of 8 products.    
                    - Present eight product recommendations based on gathered information.
                    - Ask for user feedback on the recommendations.
                    - If the user expresses interest in seeing more options, provide another set of eight recommendations.
                    - if the user changes his interests then must re-assure the budget.
                    - Continuously refine product suggestions based on feedback.
                    - Repeat the process, presenting refined recommendations eight at a time and seeking feedback until the user indicates satisfaction or makes specific changes to preferences.
                    - Maintain a positive and engaging tone throughout the interaction.
                   
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
    # insert_global_token_stats(token_info)
    return session_memory.buffer[-1].content


def question_or_recommendation(ai_response):
    response_schemas = [ResponseSchema(name="flag", description="bool value true or false")]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    flag_prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                **Role:**
                    Imagine you're a skilled text analyzer tasked with determining if responses suggest questions or product recommendations.

                Response = {ai_response}
                Lets do it step by step:
                **Step 1: Careful Analysis**
                - Examine the provided response thoroughly.

                **Step 2: Identify Response Type**
                - Clearly determine if the response is inquiring about user preferences, providing a product recommendation, or asking recommendation questions.
                - Check for sentence structure ending with a question mark or containing interrogative words.
                - Search for phrases expressing preference or advice.

                **Step 3: Binary Flag Implementation**
                - Use a binary flag to capture AI behavior.
                - If the response suggests products, set the flag to 'True'; otherwise, set it to 'False.'

                **Step 4: Return the Flag**
                - Provide the resulting flag as the output.
                - Ensure the flag aligns with the type of detected response.
                - Adjust rules based on the conversational context and user-specific patterns.
                
                 \n{format_instructions}\n{ai_response}
 
    """
            )
        ],
        input_variables=["ai_response"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = flag_prompt.format_prompt(ai_response=ai_response)
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
    attr = output_parser.parse(result.content)
    # insert_global_token_stats(token_info)
 
    return attr

def products_and_features(ai_products):
    response_schemas = [ ResponseSchema(name="product name", description="list of product item"),
        ResponseSchema(name="budget", description="a dictionary with keys and values of features"),
        ResponseSchema(name="feedback", description="a descriptive sentence asking feedback on prefrences")]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    flag_prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                 **Role:**
                    Imagine you're a products and its feature analyzer tasked to extract the recommended products in the response.

                Response = {ai_products}

                Lets do it step by step:
                Step 1:
                - Carefully analyze the products given.
                Step 2:
                - Extract the recommended product item names
                Step 3:
                - Extract the budget.
                - if the budget is a vague value then convert into numerical value accordingly
                Step 4:
                - Breakdown the budget into min and max key value pairs.
                - set the min ans max value based on the range.
                - If signle amount is given set the min to 1 and max to the amount given.
                - Store the amount withut dollar sign.
                - Extract the feedback mentioned in the response
                Step 4:
                Return all the product item in a list named as 'product name' , provided budget , min amount , max amount in a dictionary named as 'budget' and feedback as sentence in variable named as 'feedback'.
               
                 \n{format_instructions}\n{ai_products}
 
    """
            )
        ],
        input_variables=["ai_products"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = flag_prompt.format_prompt(ai_products=ai_products)
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
    attr = output_parser.parse(result.content)
    # insert_global_token_stats(token_info)
 
    return attr


 
def get_attributes(ai):
    global COUNTER  # Add this line if you want to modify the global variable
    COUNTER = COUNTER + 1
    response_schemas = [
        ResponseSchema(name="product name", description="list of product item"),
        ResponseSchema(name="flag", description="bool value true or false"),
        ResponseSchema(name="features", description="a dictionary with keys and values of features"),
        ResponseSchema(name="feedback", description="a descriptive sentece asking feedback on prefrences")
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
                5. "Certainly! Here's another book recommendation for you: "To Kill a Mockingbird" by Harper Lee. It's a classic novel set in the 1930s that explores themes of racial injustice, morality, and the loss of innocence. The story is told through the eyes of Scout Finch, a young girl growing up in the fictional town of Maycomb, Alabama. This book is known for its powerful storytelling and thought-provoking messages. The budget range for this book is typically around $10 to $20."
                6. "Certainly! Here's another book recommendation for you: "The Catcher in the Rye" by J.D. Salinger. It's a classic coming-of-age novel that follows the story of Holden Caulfield, a disillusioned teenager navigating the complexities of adulthood and society. This book is known for its introspective narrative and exploration of themes such as identity, alienation, and the loss of innocence. The budget range for this book is typically around $10 to $20."
               
               
               
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
                - Breakdown the budget into min and max key value pairs.
                - set the min ans max value based on the range.
                - If signle amount is given set the min to 1 and max to the amount given.
                - Breakdown the budget into min and max key value pairs.
                - set the min ans max value based on the range.
                - If signle amount is given set the min to 1 and max to the amount given.
                - Systematically organize the extracted feature values into a dictionary.
                - Store the amount withut dollar sign.
                - Ensure each feature is paired with its corresponding value, including keys like 'budget,' 'min,' 'max,' and any other relevant keys.
                - Extract the feedback mentioned in the ai response.
 
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
    # insert_global_token_stats(token_info)
 
    return attr
 
def example_response( ai_response):
    global COUNTER  # Add this line if you want to modify the global variable
    COUNTER = COUNTER + 1
    response_schemas = [
        ResponseSchema(name="example", description="list of strings of example responses")
    ]
 
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
 
    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
              **Role:**
- Assume the persona of an answer generator, an efficient and knowledgeable virtual assistant committed to delivering concise, accurate, and user-focused responses across a wide range of inquiries.
Question: {ai_response}

**Lets do it step by step:**

**Steps for Generating Sample Answers:**

**Step 1. Analyze the Question:**
- Carefully examine the question to fully understand its meaning.
- Consider the context to ensure accurate and relevant responses.

**Step 2. Generate 8 Responses:**
- Create concise responses with a maximum of 1 to 2 words each.
- Ensure the responses are literal and directly address the question.
- Avoid forming questions in the responses.
- Maintain alignment between all 8 responses.
- Do not give vague responses for budget question.

**Step 3. Verify Context Alignment:**
- After generating responses, cross-verify them with existing knowledge.
- Ensure that the answers align with the context of the original question.
- Confirm that each response is relevant to the preferences of the product.

**Step 4. Return as 'example' List:**
- Compile the 8 responses into a list named 'example' for easy reference.


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
    # insert_global_token_stats(token_info)
 
    return attr
 
def change_tone( ai_input):
    global COUNTER  # Add this line if you want to modify the global variable
    COUNTER = COUNTER + 1
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
    # insert_global_token_stats(token_info)
 
    return attr
 
 
def conversation_title( conversation):
    global COUNTER  # Add this line if you want to modify the global variable
    COUNTER = COUNTER + 1
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
    # insert_global_token_stats(token_info)
 
    return title
 
 
# sub_categories =['Kindle Kids', 'Kindle Paperwhite', 'Kindle Oasis', 'Kindle Books', 'Camera & Photo', 'Headphones', 'Video Game Consoles & Accessories', 'Wearable Technology', 'Cell Phones & Accessories', 'Computer Accessories & Peripherals', 'Monitors', 'Laptop Accessories', 'Data Storage', 'Amazon Smart Home', 'Smart Home Lighting', 'Smart Locks and Entry', 'Security Cameras and Systems', 'Painting, Drawing & Art Supplies', 'Beading & Jewelry Making', 'Crafting', 'Sewing', 'Car Care', 'Car Electronics & Accessories', 'Exterior Accessories', 'Interior Accessories', 'Motorcycle & Powersports', 'Activity & Entertainment', 'Apparel & Accessories', 'Baby & Toddler Toys', 'Nursery', 'Travel Gear', 'Makeup', 'Skin Care', 'Hair Care', 'Fragrance', 'Foot, Hand & Nail Care', 'Clothing', 'Shoes', 'Jewelry', 'Watches', 'Handbags', 'Clothing', 'Shoes', 'Watches', 'Accessories', 'Clothing', 'Shoes', 'Jewelry', 'Watches', 'Handbags', 'Clothing', 'Shoes', 'Jewelry', 'Watches', 'Health Care', 'Household Supplies', 'Vitamins & Dietary Supplements', 'Wellness & Relaxation', 'Kitchen & Dining', 'Bedding', 'Bath', 'Furniture', 'Home Décor', 'Wall Art', 'Carry-ons', 'Backpacks', 'Garment bags', 'Travel Totes', 'Dogs', 'Cats', 'Fish & Aquatic Pets', 'Birds', 'Sports and Outdoors', 'Outdoor Recreation', 'Sports & Fitness', 'Tools & Home Improvement', 'Appliances', 'Building Supplies', 'Electrical', 'Action Figures & Statues', 'Arts & Crafts', 'Baby & Toddler Toys', 'Building Toys', 'Video Games', 'PlayStation', 'Xbox', 'Nintendo', 'PC', 'All gift cards', 'eGift cards', 'Gift cards by mail', 'Specialty gift cards']
 
def product_response( product , category):
    global COUNTER  # Add this line if you want to modify the global variable
    COUNTER = COUNTER + 1
    response_schemas = [
        ResponseSchema(name="Categories", description="a key value of most relevant category and sub category")]
 
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
 
    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
               """
                *Role:*
                - Picture yourself as an AI guide, assisting users in finding the perfect category of products.
                - Your mission is to thoughtfully analyze the products and align them with the provided categories .
 
                *Products:* {product}
                *Categories List:* {category}
 
                *Let's Think Step by Step:*
                1. First, carefully identify each product with its descrirption provided.
                2. Next, determine under which category of given list of category each product falls.
                3. Lastly, assign one suitable category from given list of categories to each product provided.
                *Output:*
                - Your output should be a dictionary containing product item name and it assigned category.
                Format:
                Product Name : Category

                return the dictionary in the provided format named as 'Categories'
 
               
                \n{format_instructions}\n{product}
                """
            )
        ],
        input_variables=["product" , "category"],
        partial_variables={"format_instructions": format_instructions}
    )
    _input = prompt2.format_prompt(product=product , category = category)
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
    # insert_global_token_stats(token_info)
 
    return attr
 
def get_products( product , min , max ):
    result = multiple_items(product , min , max)
    return result
   
def get_amazon_products(product, min , max):
    try:
        return get_products(product, min , max)
    except Exception as e:
        print("error from amazon", e)
        return {"search_result": {"items": []}}

def get_title(memory_dict, session_id):
    try:
        title = conversation_title(memory_dict[session_id].buffer)
        return title.get('Title')
    except Exception as e:
        return None
    
def extract_budget_range(budget_string):
    # Define a regular expression pattern for extracting the budget range
    range_pattern = re.compile(r'\$([\d,]+)-\$([\d,]+)')

    # Attempt to match the range format
    match = range_pattern.match(budget_string)
    if match:
        # Extract and clean the min and max values
        min_value = int(match.group(1).replace(',', ''))
        max_value = int(match.group(2).replace(',', ''))
    else:
        # If the pattern is not matched, set default values
        min_value = 1
        max_value = 500

    return min_value, max_value
 
search_indexes = [ "AmazonVideo", "Apparel", "Appliances", "ArtsAndCrafts", "Automotive", "Baby", "Beauty", "Books", "Classical", "Collectibles", "Computers", "DigitalMusic", "DigitalEducationalResources", "Electronics", "EverythingElse", "Fashion", "FashionBaby", "FashionBoys", "FashionGirls", "FashionMen", "FashionWomen", "GardenAndOutdoor", "GiftCards", "GroceryAndGourmetFood", "Handmade", "HealthPersonalCare", "HomeAndKitchen", "Industrial", "Jewelry", "KindleStore", "LocalServices", "Luggage", "LuxuryBeauty", "Magazines", "MobileAndAccessories", "MobileApps", "MoviesAndTV", "Music", "MusicalInstruments", "OfficeProducts", "PetSupplies", "Photo", "Shoes", "Software", "SportsAndOutdoors", "ToolsAndHomeImprovement", "ToysAndGames", "VHS", "VideoGames", "Watches"]
def output_filteration(output_old, flag  ,session_id):
    json = {}
    errors = ""
    
   
    if flag == "True" or flag == "true" or flag == True:
        # try:
        #     parser1 = products_and_features( output_old)
        # except Exception as e:
        #     parser1 = {"product": [] , "features": {} , "feedback" : ""}

        # product = parser1.get('product name')
        # # print(parser1)
    
        feedback = output_old.strip().split('\n')[-1]     # extract feedback from llm 
        product = re.findall(r'Product Name \d+: (.+?)(?:\n|$)', output_old) # extract products names from llm 
        first_budget_match = re.search(r'Budget Provided: (\$.+)', output_old)# extract prices from llm 
        
        # Extract and store the budget range
        if first_budget_match:
            budget_range = extract_budget_range(first_budget_match.group(1))
            min = budget_range[0]
            max = budget_range[1]
            print(f"First Product Budget Range: Min = {budget_range[0]}, Max = {budget_range[1]}")
        else:
            min = None
            max = None
            print("No budget information found.")

        # print(product_response(product , search_indexes))
        

        # print(product)

        # print("total products: ",len(product))
        if len(product) >=1:
            output = "Certainly, allow me to engage in a brainstorming session to generate ideas. 🧠💡 "

            

            try:
                amazon , no , error = get_products( product , min , max)
                errors = error
                
                print(amazon,no , error)
            except Exception as e:
                
                print("error from amazon",e)
            # print("total products from amazon: ",len(amazon["search_result"]["items"]))

            #check for error from amazon
            if no == None:
                
                output = "Oops! Something went wrong and we could not process your request. Please try again!"
                json["Product"] = {}
                json["error"] = errors
                json["result"] = output
                json["example"] = []
                json["session_id"] = session_id
                print("in no")
                return json
            else:
                print("in else")
                if (len(amazon["search_result"]["items"])==0):
                    output = "Apologies! 😞 No products were found. Let's try a new search from the beginning. 🔍"
                    json["Product"] = {}
                    json["result"] = output
                    json["example"] = []
                    json["session_id"] = session_id
                    print("in len 0")
                    return json
                else:
                    print("in len >1")
                    try:
                        title = conversation_title(memory_dict[session_id].buffer)
                        new = title.get('Title')
                    except Exception as e:
                        new = None
            
                    json["Product"] = amazon
                    json["example"] = []
                    json["result"] = output
                    json["session_id"] = session_id

                    json["Title"] = new
                    json["feedback"] = feedback 
                    return json
        else:
            try:
                parser2 = example_response(output_old)
            except Exception as e:
                print("here", str(e))
                parser2 = {"example": ['']}

            # get example responses from example responses function
            example_answers = parser2.get('example', [])
            example_answers_unique = set(example_answers)
            unique_example_answers = list(example_answers_unique)
            if example_answers == ['']:
                example_answers= []

            json["Product"] = {}
            json["result"] = output_old
            json["example"] = unique_example_answers
            json["session_id"] = session_id
    else:
        try:
            parser2 = example_response(output_old)
        except Exception as e:
            print("here", str(e))
            parser2 = {"example": ['']}

        # get example responses from example responses function
        example_answers = parser2.get('example', [])

        example_answers_unique = set(example_answers)
        unique_example_answers = list(example_answers_unique)
        # print(unique_example_answers)
        if example_answers == ['']:
            example_answers= []

        json["Product"] = {}
        json["result"] = output_old
        json["example"] = unique_example_answers
        json["session_id"] = session_id
        # print(memory_dict[session_id].buffer)
    
 
    return json
 
def main_input(user_input, user_session_id):
    session_memory = get_or_create_memory_for_session(user_session_id)
    # output = initial_chat(user_input, session_memory )
    try:
        output = initial_chat(user_input, session_memory )
    except Exception as e:
        output = {"error": "Something Went Wrong ...." , "code": "500"}
        return output
    strings_to_find = ["I'll find","Ill find","I Will Find", "Give me a moment", "One moment", "hold for a moment" , "for a moment" , "I'll be right back" , "Ill be right back" , "I'll be right back with some options" , "Ill be right back with some options"  , "just a moment" , "Ill get right on it" , " I'll get right on it"]
    

    translator = str.maketrans("", "", string.punctuation)
    lowercase_sentence = output.translate(translator).lower()
    found_strings = [string for string in strings_to_find if string.lower() in lowercase_sentence]
    if found_strings:
        print("buffer here..." , found_strings)
        output = initial_chat("ok , suggest products",session_memory)
    if output.count("Product Name") >=1 and output.count("Budget Provided")>=1:
        gflag = "True"
        print("main flag",gflag)
    else:
        gflag = "False"
        # print("main flag",gflag)
 
    final_output = output_filteration( output, gflag, user_session_id)
 
    return final_output

# for i in range(5):
#     inp = input()
#     print(main_input(inp,"0"))
tt = """

- Product Name 1: Creed Aventus Eau de Parfum
- Budget Provided: $200
- Product Name 2: Tom Ford Noir Extreme
- Budget Provided: $200
- Product Name 3: Acqua Di Gio Profumo by Giorgio Armani
- Budget Provided: $200
- Product Name 4: Bvlgari Man in Black Eau de Parfum
- Budget Provided: $200
- Product Name 5: Montblanc Explorer Eau de Parfum
- Budget Provided: $200
- Product Name 6: Viktor&Rolf Spicebomb Extreme Eau de Parfum
- Budget Provided: $200
- Product Name 7: Dior Sauvage Eau de Toilette
- Budget Provided: $200
- Product Name 8: Versace Eros Flame Eau de Parfum
- Budget Provided: $200

Do any of these catch your eye for your brother's birthday gift? 🎁✨
"""
# print(output_filteration(tt , "True" , "0"))