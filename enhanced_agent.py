"""
Enhanced Azure OpenAI Agent with multiple tools:
- DuckDuckGo Web Search
- Python Code Interpreter  
- C# Code Search and Analysis
"""

import os
import json
import sys
import io
import contextlib
from openai import AzureOpenAI
from ddgs import DDGS
from code_search_tool import CSharpCodeSearcher, create_code_search_tool_function, execute_code_search
import agent_config as config

# Configuration
class AgentConfig:
    """Configuration for the enhanced agent - uses external config file"""
    
    # Azure OpenAI Settings
    AZURE_ENDPOINT = "<endpoint>"
    AZURE_API_KEY = "<apikey>"
    AZURE_API_VERSION = "2024-10-21"
    MODEL_NAME = "gpt-4o-mini"
    
    # C# Project Settings - imported from agent_config.py
    CSHARP_PROJECT_PATH = getattr(config, 'CSHARP_PROJECT_PATH', r"C:\Path\To\Your\CSharp\Project")
    SKIP_FOLDERS = getattr(config, 'SKIP_FOLDERS', [
        'bin', 'obj', '.vs', '.git', '.svn', 'packages', 
        'node_modules', 'Debug', 'Release', '.vscode', 'TestResults'
    ])
    
    # Tool Settings - imported from agent_config.py
    MAX_SEARCH_RESULTS = getattr(config, 'MAX_SEARCH_RESULTS', 25)
    MAX_CODE_CONTEXT_LINES = getattr(config, 'MAX_CODE_CONTEXT_LINES', 5)
    MAX_FILE_SIZE_MB = getattr(config, 'MAX_FILE_SIZE_MB', 10.0)

class EnhancedAgent:
    """Enhanced AI Agent with multiple capabilities"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=config.AZURE_ENDPOINT,
            api_key=config.AZURE_API_KEY,
            api_version=config.AZURE_API_VERSION
        )
        
        # Initialize C# Code Searcher
        try:
            self.code_searcher = CSharpCodeSearcher(
                code_folder_path=config.CSHARP_PROJECT_PATH,
                skip_folders=config.SKIP_FOLDERS,
                max_file_size_mb=config.MAX_FILE_SIZE_MB
            )
            self.code_search_available = True
        except Exception as e:
            print(f"⚠️ Warning: C# Code Search not available: {e}")
            self.code_search_available = False
        
        # Define available tools
        self.tools = self._create_tools()
    
    def _create_tools(self):
        """Create the tool definitions"""
        tools = [
            # Web Search Tool
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web using DuckDuckGo for current information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            # Code Interpreter Tool
            {
                "type": "function",
                "function": {
                    "name": "code_interpreter",
                    "description": "Execute Python code for calculations, data analysis, or computations",
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
        
        # Add C# Code Search tool if available
        if self.code_search_available:
            tools.append(create_code_search_tool_function(
                self.config.CSHARP_PROJECT_PATH, 
                self.config.SKIP_FOLDERS
            ))
        
        return tools
    
    def web_search(self, query: str, max_results: int = 5) -> str:
        """Execute web search using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                
                if not results:
                    return f"No web results found for: {query}"
                
                formatted_results = f"Web search results for '{query}':\n\n"
                
                for i, result in enumerate(results, 1):
                    formatted_results += f"{i}. **{result.get('title', 'No title')}**\n"
                    formatted_results += f"   {result.get('body', 'No description')}\n"
                    formatted_results += f"   URL: {result.get('href', 'No URL')}\n\n"
                
                return formatted_results
                
        except Exception as e:
            return f"Web search error: {str(e)}"
    
    def code_interpreter(self, code: str) -> str:
        """Execute Python code safely"""
        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured = io.StringIO()
            
            # Create safe namespace with common imports
            namespace = {
                'math': __import__('math'),
                'random': __import__('random'),
                'datetime': __import__('datetime'),
                'json': __import__('json'),
                'os': __import__('os'),
                're': __import__('re'),
            }
            
            try:
                # Try evaluation first for expressions
                result = eval(code, {"__builtins__": __builtins__}, namespace)
                if result is not None:
                    print(result)
            except:
                # If eval fails, execute as statements
                exec(code, {"__builtins__": __builtins__}, namespace)
            
            # Get output
            output = captured.getvalue()
            sys.stdout = old_stdout
            
            return f"Code Output:\n{output}" if output else "Code executed successfully (no output)"
            
        except Exception as e:
            sys.stdout = old_stdout
            return f"Code execution error: {str(e)}"
    
    def execute_tool_call(self, tool_call):
        """Execute a tool call and return the result"""
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        if function_name == "web_search":
            query = function_args.get("query", "")
            print(f"🔍 Searching web for: {query}")
            return self.web_search(query)
        
        elif function_name == "code_interpreter":
            code = function_args.get("code", "")
            print(f"💻 Executing Python code:")
            print(f"```python\n{code}\n```")
            return self.code_interpreter(code)
        
        elif function_name == "code_search" and self.code_search_available:
            action = function_args.get("action", "search")
            query = function_args.get("query", "")
            print(f"📂 Performing C# code {action}: {query}")
            return execute_code_search(self.code_searcher, **function_args)
        
        else:
            return f"Unknown tool: {function_name}"
    
    def chat(self, user_message: str, max_iterations: int = 5) -> str:
        """
        Chat with the enhanced agent
        
        Args:
            user_message: User's message
            max_iterations: Maximum number of tool call iterations
            
        Returns:
            Agent's response
        """
        messages = [{"role": "user", "content": user_message}]
        iteration = 0
        
        while iteration < max_iterations:
            # Call the model
            response = self.client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Check if the model wants to call tools
            if response_message.tool_calls:
                # Add the assistant's message with tool calls
                messages.append(response_message)
                
                # Execute each tool call
                for tool_call in response_message.tool_calls:
                    tool_result = self.execute_tool_call(tool_call)
                    
                    # Add the tool result to messages
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call.id
                    })
                
                iteration += 1
            else:
                # No tool calls, return the response
                return response_message.content
        
        # If we've reached max iterations, make one final call
        final_response = self.client.chat.completions.create(
            model=self.config.MODEL_NAME,
            messages=messages
        )
        
        return final_response.choices[0].message.content
    
    def get_capabilities(self) -> str:
        """Return a description of agent capabilities"""
        capabilities = [
            "🔍 **Web Search**: Search current information using DuckDuckGo",
            "💻 **Code Interpreter**: Execute Python code for calculations and analysis",
        ]
        
        if self.code_search_available:
            capabilities.append("📂 **C# Code Search**: Search and analyze your C# codebase")
        else:
            capabilities.append("📂 **C# Code Search**: ⚠️ Not configured (update CSHARP_PROJECT_PATH)")
        
        return "\n".join(capabilities)


def main():
    """Main interactive loop"""
    config = AgentConfig()
    agent = EnhancedAgent(config)
    
    print("🤖 Enhanced Azure OpenAI Agent")
    print("=" * 50)
    print("Capabilities:")
    print(agent.get_capabilities())
    print("\nExample questions:")
    print("• 'Search for latest AI news'")
    print("• 'Calculate the factorial of 20'")
    print("• 'Find all classes in my C# project that contain User'")
    print("• 'Show me the structure of my C# project'")
    print("• 'What methods are in the UserService class?'")
    print("\nType 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print(f"\n🤖 AI Agent:")
            response = agent.chat(user_input)
            print(response)
            print("\n" + "-" * 70 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
