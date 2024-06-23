import chainlit as cl
import requests
import ast
import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy import insert
import pandas as pd

user = 'root'
password = 'root'
host = '127.0.0.1'
port = 3306
database = 'chatbot'

def get_connection():
    return create_engine(
        url="mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(
            user, password, host, port, database
        )
    )
    
engine = get_connection()
conn = engine.connect()

#global user_id, user_selected_product, user_confirmation, func_to_call



@cl.on_message
async def on_message(message: cl.Message):
    user_id = cl.user_session.get("user_id")
    if user_id == None:
        user_id = await cl.AskActionMessage(
        content="Pick a user for simulation",
        actions=[
            cl.Action(name="user id 1", value="1", label="Biden"),
            cl.Action(name="user id 2", value="2", label="Putin"),
            cl.Action(name="user id 2", value="6", label="Sachin"),
            ],
        ).send()
    else:
        USER_ID = user_id
        text = message.content
    
        response = requests.get('http://127.0.0.1:8001/backend_call', params={'USER_ID': USER_ID,
                                                                   'text' : text,
                                                                   'user_selected_product' : cl.user_session.get("user_selected_product"),
                                                                   'user_confirmation' : cl.user_session.get("user_confirmation"),
                                                                   'func_to_call' : cl.user_session.get("func_to_call")
                                                                   })
        response = response.json()
        msg = response.get('message', None)
        order_ids = response.get('orders', [])
        resp_type = response.get('resp_type', '')
        function_to_call = response.get('function_to_call', '')
        
        if len(order_ids) > 0:
            #user_products = pd.read_sql(f"SELECT * FROM user_products WHERE user_id = {USER_ID} AND order_id IN {tuple(order_ids + order_ids)}", conn)
            user_products = pd.read_csv('user_products.csv')
            user_products = user_products[(user_products.user_id == int(USER_ID)) & (user_products.order_id.isin(order_ids))]
            actions = []
            for u in range(len(user_products)):
                order_id = user_products['order_id'].iloc[u]
                description = user_products['description'].iloc[u]
                purchased_at = str(user_products['purchased_at'].iloc[u])
                
                actions.append(cl.Action(name=str(order_id), value=str(order_id), label=f"{description} purchased at {str(purchased_at)}"))
            
            resp = await cl.AskActionMessage(
                    content="Select a product from below to confirm, Or describe the product you want help with",
                    actions = actions
                    ).send()
            
            if str(type(resp)) == "<class 'dict'>":
                cl.user_session.set("user_selected_product", str(resp.get('value', '')))
                product_name = str(resp.get('label', ''))
                msg = f'Please tell me what I can help you with {product_name}\nI can help you with cancellation, return of product and many more'
        
        
        
        if (resp_type == 'get_cofirmation') & (function_to_call in ['CancelOrder', 'ReturnOrder', 'ReplaceOrder']):
            if function_to_call == 'CancelOrder':
                print('cancelling order')
                resp = await cl.AskActionMessage(
                content="Please confirm if you want to cancel this order.",
                actions=[
                    cl.Action(name="Yes", value="true", label=f"Yes I want to cancel product {cl.user_session.get("user_selected_product")}"),
                    cl.Action(name="No", value="false", label="No I dont want to cancel it"),
                    ],
                timeout = 1000
                    ).send()
                response = requests.get('http://127.0.0.1:8001/backend_call', params={'USER_ID': USER_ID,
                                                                   'text' : text,
                                                                   'user_selected_product' : cl.user_session.get("user_selected_product"),
                                                                   'user_confirmation' : resp['value'],
                                                                   'func_to_call' : function_to_call
                                                                   })
                
                response = response.json()
                msg = response.get('message', None)
                print(msg)
                resp_type = response.get('resp_type', None)
                
            
            if function_to_call == 'ReturnOrder':
                print('returning order')
                resp = await cl.AskActionMessage(
                content="Please confirm if you want to return this order",
                actions=[
                    cl.Action(name="Yes", value="true", label=f"Yes I want to return product {cl.user_session.get("user_selected_product")}"),
                    cl.Action(name="No", value="false", label="No I dont want to return it"),
                    ],
                    ).send()
                
                response = requests.get('http://127.0.0.1:8001/backend_call', params={'USER_ID': USER_ID,
                                                                   'text' : text,
                                                                   'user_selected_product' : cl.user_session.get("user_selected_product"),
                                                                   'user_confirmation' : resp['value'],
                                                                   'func_to_call' : function_to_call
                                                                   })
                
                response = response.json()
                msg = response.get('message', None)
                print(msg)
                resp_type = response.get('resp_type', None)
                
            if function_to_call == 'ReplaceOrder':
                print('replacing order')
                resp = await cl.AskActionMessage(
                content="Please confirm if you want to replace this order!",
                actions=[
                    cl.Action(name="Yes", value="true", label=f"Yes I want to replace product {cl.user_session.get("user_selected_product")}"),
                    cl.Action(name="No", value="false", label="No I dont want to relace it"),
                    ],
                    ).send()
                
                response = requests.get('http://127.0.0.1:8001/backend_call', params={'USER_ID': USER_ID,
                                                                   'text' : text,
                                                                   'user_selected_product' : cl.user_session.get("user_selected_product"),
                                                                   'user_confirmation' : resp['value'],
                                                                   'func_to_call' : function_to_call
                                                                   })
                
                response = response.json()
                msg = response.get('message', None)
                print(msg)
                resp_type = response.get('resp_type', None)
                
            if resp_type == 'tool_msg':
                print('tool_message')
                resp = await cl.AskActionMessage(
                    content=msg,
                    actions=[
                        cl.Action(name="3", value="same_product", label="I need more support on same product"),
                        cl.Action(name="4", value="different_product", label="I need help with some other product"),
                        cl.Action(name="1", value="session_end", label=f"My queries are solved"),
                        cl.Action(name="2", value="need_human_help", label="I am not happy, I want to connect with a human agent"),
                        ],
                    ).send()
                print(resp['value'])
                if str(type(resp)) == "<class 'dict'>":  
                    if resp['value'] == 'different_product':
                        cl.user_session.set("user_selected_product", None)
                        msg = "please describe the product you want help with"
                        await cl.Message(msg).send()
                    elif resp['value'] == 'same_product':
                        msg = "Please tell me how I can help with this order"
                        await cl.Message(msg).send()
                    elif resp['value'] == 'session_end':
                        msg = "Thank you for talking to me, Have a great day!"
                        await cl.Message(msg).send()
                    elif resp['value'] == 'need_human_help':
                        msg = "One of our attendent will join the chat soon, please wait."
                        await cl.Message(msg).send()
        
        if resp_type == 'tool_msg':
            print('tool_message direct')
            resp = await cl.AskActionMessage(
                content=msg,
                actions=[
                    cl.Action(name="3", value="same_product", label="I need more support on same product"),
                    cl.Action(name="4", value="different_product", label="I need help with some other product"),
                    cl.Action(name="1", value="session_end", label=f"My queries are solved"),
                    cl.Action(name="2", value="need_human_help", label="I am not happy, I want to connect with a human agent"),
                    ],
                ).send()
            print(resp['value'])
            if str(type(resp)) == "<class 'dict'>":  
                if resp['value'] == 'different_product':
                    cl.user_session.set("user_selected_product", None)
                    msg = "please describe the product you want help with"
                    await cl.Message(msg).send()
                elif resp['value'] == 'same_product':
                    msg = "Please tell me how I can help with this order"
                    await cl.Message(msg).send()
                elif resp['value'] == 'session_end':
                    msg = "Thank you for talking to me, Have a great day!"
                    await cl.Message(msg).send()
                elif resp['value'] == 'need_human_help':
                    msg = "One of our attendent will join the chat soon, please wait."
                    await cl.Message(msg).send()        
            
        
    await cl.Message(msg).send()

@cl.on_chat_start
async def main():
    
    cl.user_session.set("user_id", None)
    cl.user_session.set("user_selected_product", None)
    cl.user_session.set("user_confirmation", None)
    cl.user_session.set("func_to_call", None)
    
    resp = await cl.AskActionMessage(
        content="Pick a user for simulation!",
        actions=[
            cl.Action(name="user id 1", value="1", label="Biden"),
            cl.Action(name="user id 2", value="2", label="Putin"),
            cl.Action(name="user id 2", value="6", label="Sachin"),
        ],
    ).send()
    
    if str(type(resp)) == "<class 'dict'>":
    
        cl.user_session.set("user_id", int(resp.get('value', None))
        )
    
    