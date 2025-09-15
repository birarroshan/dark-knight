# Enhanced Agent Configuration
# Update these settings for your environment

# C# Project Configuration
CSHARP_PROJECT_PATH = r"C:\Work\DMO\obrepo\build\src\SoDAutomation\build\src\SoDTestBDD\BDDFoundation"  # UPDATE THIS PATH

# Folders to skip during code search (add/remove as needed)
SKIP_FOLDERS = [
    'bin',           # Binary output
    'obj',           # Object files  
    '.vs',           # Visual Studio
    '.git',          # Git repository
    '.svn',          # SVN repository
    'packages',      # NuGet packages
    'node_modules',  # Node.js modules
    'Debug',         # Debug build
    'Release',       # Release build
    '.vscode',       # VS Code settings
    'TestResults',   # Test results
    'artifacts',     # Build artifacts
    '.nuget',        # NuGet cache
    'wwwroot/lib'    # Web libraries
]

# File extensions to include in search
FILE_EXTENSIONS = [
    '.cs',           # C# source files
    '.csx',          # C# script files
    '.cshtml',       # Razor views
    '.razor',        # Blazor components
    '.xaml',         # XAML files
    '.config',       # Configuration files
    '.json',         # JSON files
    '.xml',          # XML files
    '.yml',          # YAML files
    '.yaml',         # YAML files
    '.sql',          # SQL files
    '.md',           # Markdown files
    '.txt',          # Text files
    '.sln',          # Solution files
    '.csproj',       # Project files
    '.props',        # MSBuild props
    '.targets'       # MSBuild targets
]

# Search Settings
MAX_SEARCH_RESULTS = 250
MAX_CODE_CONTEXT_LINES = 50
MAX_FILE_SIZE_MB = 10.0

# Examples of what you can ask:
EXAMPLE_QUERIES = [
    # Code Search Examples
    "Find all classes that inherit from Controller",
    "Show me methods that contain 'async' in UserService",
    "Search for 'database connection' in my code",
    "What files contain the word 'authentication'?",
    "Show me the structure of my project",
    "Find all classes with 'Repository' in the name",
    "Get the content of Controllers/HomeController.cs",
    
    # Web Search Examples  
    "What are the latest .NET updates?",
    "Search for C# best practices 2025",
    "Find current ASP.NET Core security recommendations",
    
    # Code Interpreter Examples
    "Calculate how many days until Christmas",
    "Generate 10 random GUIDs",
    "Convert JSON to C# class properties",
    "Parse this connection string and show components"
]
