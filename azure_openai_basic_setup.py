import os
from openai import AzureOpenAI
import json

# Set your Azure OpenAI endpoint and key
client = AzureOpenAI(
    azure_endpoint="<endpoint>",
    api_key="<apikey>",
    api_version="2024-10-21"
)

# Define the Bing grounding tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "bing_grounding",
            "description": "Search the web using Bing to get current information and ground responses with real-time data",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to send to Bing"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def bing_search(query):
    """Simple mock function for Bing search - replace with actual Bing API call"""
    return f"Search results for '{query}': [Mock results - integrate with Bing Search API for real results]"

# Example: Send a prompt with tool calling capability
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "What's the latest news about AI developments? Please search for current information."}
    ],
    tools=tools,
    tool_choice="auto"  # Let the model decide when to use tools
)

# Check if the model wants to call a tool
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    if tool_call.function.name == "bing_grounding":
        # Parse the function arguments
        function_args = json.loads(tool_call.function.arguments)
        query = function_args["query"]
        
        # Call our search function
        search_results = bing_search(query)
        
        # Send the search results back to the model
        messages = [
            {"role": "user", "content": "What's the latest news about AI developments? Please search for current information."},
            response.choices[0].message,  # Assistant's tool call
            {
                "role": "tool",
                "content": search_results,
                "tool_call_id": tool_call.id
            }
        ]
        
        # Get the final response with grounded information
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        print("Agent response with grounding:", final_response.choices[0].message.content)
    else:
        print("Agent response:", response.choices[0].message.content)
else:
    print("Agent response:", response.choices[0].message.content)
