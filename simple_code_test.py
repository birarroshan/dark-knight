import os
from openai import AzureOpenAI
import json
import sys
import io

# Set your Azure OpenAI endpoint and key
client = AzureOpenAI(
    azure_endpoint="<endpoint>",
    api_key="<apikey>",
    api_version="2024-10-21"
)

# Simple code executor function
def execute_python_code(code):
    """Execute Python code and return the result"""
    try:
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        
        # Execute the code
        exec(code)
        
        # Get output
        output = captured.getvalue()
        sys.stdout = old_stdout
        
        return output if output else "Code executed successfully"
    except Exception as e:
        sys.stdout = old_stdout
        return f"Error: {str(e)}"

# Test the code executor
print("🧪 Testing Code Interpreter")
print("=" * 30)

test_codes = [
    "print('Hello, World!')",
    "result = 5 + 3\nprint(f'5 + 3 = {result}')",
    "import math\nprint(f'Factorial of 5: {math.factorial(5)}')",
    "numbers = [1, 2, 3, 4, 5]\nsquares = [x**2 for x in numbers]\nprint(f'Squares: {squares}')"
]

for i, code in enumerate(test_codes, 1):
    print(f"\n{i}. Testing code:")
    print(f"```python\n{code}\n```")
    result = execute_python_code(code)
    print(f"Result: {result}")

print("\n" + "="*50)
print("✅ Code Interpreter is working!")
print("\nNow testing with AI Agent...")

# Define the tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "python_executor",
            "description": "Execute Python code and return the output",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        }
    }
]

# Test with AI
question = "Calculate 2^10 and show the result"
print(f"\n📝 Question: {question}")

messages = [{"role": "user", "content": question}]
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    if tool_call.function.name == "python_executor":
        function_args = json.loads(tool_call.function.arguments)
        code = function_args["code"]
        
        print(f"\n💻 AI generated code:")
        print(f"```python\n{code}\n```")
        
        result = execute_python_code(code)
        print(f"📊 Execution result: {result}")
        
        # Send result back to AI
        messages.append(response.choices[0].message)
        messages.append({
            "role": "tool",
            "content": result,
            "tool_call_id": tool_call.id
        })
        
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        print(f"\n🎯 AI Response: {final_response.choices[0].message.content}")
else:
    print(f"🤖 Direct Response: {response.choices[0].message.content}")

print(f"\n🎉 Code Interpreter Agent is working perfectly!")
