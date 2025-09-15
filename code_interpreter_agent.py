import os
from openai import AzureOpenAI
import json
import sys
import io
import contextlib
import traceback

# Set your Azure OpenAI endpoint and key
client = AzureOpenAI(
    azure_endpoint="<endpoint>",
    api_key="<apikey>",
    api_version="2024-10-21"
)

# Define the code interpreter tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "code_interpreter",
            "description": "Execute Python code and return the output. Use this for calculations, data analysis, or any computational tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to execute"
                    }
                },
                "required": ["code"]
            }
        }
    }
]

def code_interpreter(code):
    """Execute Python code and return results"""
    try:
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        # Create namespace with common imports
        namespace = {
            'math': __import__('math'),
            'random': __import__('random'),
            'datetime': __import__('datetime'),
            'json': __import__('json'),
        }
        
        # Try to evaluate as expression first (for single values)
        try:
            result = eval(code, {"__builtins__": __builtins__}, namespace)
            if result is not None:
                print(result)
        except:
            # If eval fails, execute as statements
            exec(code, {"__builtins__": __builtins__}, namespace)
        
        # Get the captured output
        output = captured_output.getvalue()
        
        # Restore stdout
        sys.stdout = old_stdout
        
        return f"Output:\n{output}" if output else "Code executed successfully"
        
    except Exception as e:
        # Restore stdout in case of error
        sys.stdout = old_stdout
        return f"Error: {str(e)}"

def chat_with_code_interpreter(user_message):
    """Chat with code interpreter capability"""
    messages = [{"role": "user", "content": user_message}]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    # Process tool calls
    if response.choices[0].message.tool_calls:
        messages.append(response.choices[0].message)
        
        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "code_interpreter":
                function_args = json.loads(tool_call.function.arguments)
                code = function_args["code"]
                
                print(f"💻 Executing code:")
                print(f"```python\n{code}\n```")
                
                # Execute code
                result = code_interpreter(code)
                print(f"📊 Result: {result}")
                
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call.id
                })
        
        # Get final response
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        return final_response.choices[0].message.content
    
    return response.choices[0].message.content

if __name__ == "__main__":
    print("🤖 Azure OpenAI Agent with Code Interpreter")
    print("=" * 45)
    print("Ask me to do calculations, data analysis, or run Python code!")
    print("Examples:")
    print("- Calculate 15 factorial")
    print("- Generate 10 random numbers")
    print("- Create a list of prime numbers up to 50")
    print("- What's 2^100?")
    print("\nType 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        print(f"\n🤖 AI Agent:")
        try:
            response = chat_with_code_interpreter(user_input)
            print(response)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "-" * 50 + "\n")
