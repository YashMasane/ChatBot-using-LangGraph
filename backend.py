from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.graph import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv
import sqlite3
import requests
import os

load_dotenv()
stock_api_key = os.getenv('STOCK_API')

model = ChatOpenAI()


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# tools


search_tool = DuckDuckGoSearchRun()


@tool
def calculator(first_number: float, second_number: float, operation: str) -> dict:
    """
    perform basic arithmatic operations on two numbers.
    supported operations: add, sub, div, mult

    first_number: a number,
    second_number: a number,
    operation: operation to be performed on these two numbers
    """
    try:
        if operation == 'add':
            result = first_number + second_number
        elif operation == 'sub':
            result = first_number - second_number
        elif operation == 'mult':
            result = first_number * second_number
        elif operation == 'div':
            if second_number != 0:
                result = first_number/second_number
            else:
                return {'error': 'can not divide by zero'}

        return {'first_number': first_number, 'second_number': second_number, 'operation': operation, 'result': result}

    except Exception as e:
        return {'error': str(e)}


@tool
def stock_data_tool(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={stock_api_key}"

    r = requests.get(url)
    return r.json()


tools = [search_tool, calculator, stock_data_tool]
llm_with_tools = model.bind_tools(tools)

# Nodes


def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    response = llm_with_tools.invoke(state['messages'])
    return {'messages': [response]}


tool_node = ToolNode(tools)


conn = sqlite3.connect('chatbot.db', check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')

workflow = graph.compile(checkpointer=checkpointer)


def get_thread_id():
    thread_ids = set()
    for checkpoint in checkpointer.list(None):
        thread_ids.add(checkpoint.config['configurable']['thread_id'])

    return list(thread_ids)
