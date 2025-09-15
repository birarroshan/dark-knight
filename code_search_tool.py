"""
Code Search Tool for C# Projects
Provides semantic search and analysis capabilities for large codebases
"""

import os
import json
import fnmatch
from pathlib import Path
from typing import List, Dict, Optional, Set
import re

class CSharpCodeSearcher:
    """
    A tool to search and analyze C# codebases with intelligent filtering and context extraction
    """
    
    def __init__(self, 
                 code_folder_path: str,
                 skip_folders: Optional[List[str]] = None,
                 file_extensions: Optional[List[str]] = None,
                 max_file_size_mb: float = 10.0):
        """
        Initialize the C# Code Searcher
        
        Args:
            code_folder_path: Root path to the C# project
            skip_folders: List of folder names to skip (e.g., ['bin', 'obj', '.git'])
            file_extensions: List of file extensions to include (default: C# related files)
            max_file_size_mb: Maximum file size to process in MB
        """
        self.code_folder_path = Path(code_folder_path)
        
        # Default folders to skip for C# projects
        self.skip_folders = skip_folders or [
            'bin', 'obj', '.vs', '.git', '.svn', 'packages', 
            'node_modules', 'Debug', 'Release', '.vscode'
        ]
        
        # Default file extensions for C# projects
        self.file_extensions = file_extensions or [
            '.cs', '.csx', '.cshtml', '.razor', '.xaml', 
            '.config', '.json', '.xml', '.yml', '.yaml',
            '.sql', '.md', '.txt', '.sln', '.csproj'
        ]
        
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.file_cache = {}
        
    def _should_skip_folder(self, folder_path: Path) -> bool:
        """Check if a folder should be skipped"""
        folder_name = folder_path.name.lower()
        return any(skip_pattern.lower() in folder_name for skip_pattern in self.skip_folders)
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included in the search"""
        # Check extension
        if not any(file_path.suffix.lower() == ext.lower() for ext in self.file_extensions):
            return False
        
        # Check file size
        try:
            if file_path.stat().st_size > self.max_file_size_bytes:
                return False
        except OSError:
            return False
        
        return True
    
    def scan_codebase(self) -> Dict[str, List[str]]:
        """
        Scan the codebase and return a summary of files found
        
        Returns:
            Dictionary with file categories and counts
        """
        if not self.code_folder_path.exists():
            raise FileNotFoundError(f"Code folder not found: {self.code_folder_path}")
        
        file_summary = {}
        total_files = 0
        
        for root, dirs, files in os.walk(self.code_folder_path):
            root_path = Path(root)
            
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if not self._should_skip_folder(root_path / d)]
            
            for file in files:
                file_path = root_path / file
                if self._should_include_file(file_path):
                    ext = file_path.suffix.lower()
                    if ext not in file_summary:
                        file_summary[ext] = []
                    
                    relative_path = file_path.relative_to(self.code_folder_path)
                    file_summary[ext].append(str(relative_path))
                    total_files += 1
        
        return {
            "summary": file_summary,
            "total_files": total_files,
            "project_root": str(self.code_folder_path)
        }
    
    def search_code(self, 
                   query: str, 
                   search_type: str = "content",
                   case_sensitive: bool = False,
                   max_results: int = 20,
                   context_lines: int = 3) -> Dict:
        """
        Search for code patterns in the codebase
        
        Args:
            query: Search query
            search_type: 'content', 'filename', 'class', 'method', 'variable'
            case_sensitive: Whether search should be case sensitive
            max_results: Maximum number of results to return
            context_lines: Number of context lines around each match
            
        Returns:
            Dictionary with search results
        """
        results = []
        
        try:
            for root, dirs, files in os.walk(self.code_folder_path):
                root_path = Path(root)
                
                # Skip unwanted directories
                dirs[:] = [d for d in dirs if not self._should_skip_folder(root_path / d)]
                
                for file in files:
                    file_path = root_path / file
                    if not self._should_include_file(file_path):
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        matches = self._search_in_file(
                            content, file_path, query, search_type, 
                            case_sensitive, context_lines
                        )
                        
                        results.extend(matches)
                        
                        if len(results) >= max_results:
                            break
                            
                    except Exception as e:
                        # Skip files that can't be read
                        continue
                
                if len(results) >= max_results:
                    break
                    
        except Exception as e:
            return {"error": f"Search failed: {str(e)}", "results": []}
        
        return {
            "query": query,
            "search_type": search_type,
            "total_matches": len(results),
            "results": results[:max_results]
        }
    
    def _search_in_file(self, 
                       content: str, 
                       file_path: Path, 
                       query: str, 
                       search_type: str,
                       case_sensitive: bool, 
                       context_lines: int) -> List[Dict]:
        """Search for patterns within a single file"""
        matches = []
        lines = content.split('\n')
        relative_path = file_path.relative_to(self.code_folder_path)
        
        if search_type == "filename":
            if (case_sensitive and query in file_path.name) or \
               (not case_sensitive and query.lower() in file_path.name.lower()):
                matches.append({
                    "file": str(relative_path),
                    "type": "filename",
                    "match": file_path.name,
                    "line_number": 0
                })
        
        elif search_type in ["content", "class", "method", "variable"]:
            search_patterns = self._get_search_patterns(query, search_type)
            
            for i, line in enumerate(lines, 1):
                for pattern in search_patterns:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    if re.search(pattern, line, flags):
                        # Get context lines
                        start_line = max(0, i - 1 - context_lines)
                        end_line = min(len(lines), i + context_lines)
                        context = lines[start_line:end_line]
                        
                        matches.append({
                            "file": str(relative_path),
                            "type": search_type,
                            "line_number": i,
                            "match": line.strip(),
                            "context": context,
                            "context_start_line": start_line + 1
                        })
                        break
        
        return matches
    
    def _get_search_patterns(self, query: str, search_type: str) -> List[str]:
        """Generate regex patterns based on search type"""
        escaped_query = re.escape(query)
        
        patterns = []
        
        if search_type == "content":
            patterns.append(escaped_query)
        
        elif search_type == "class":
            patterns.extend([
                rf'\bclass\s+{escaped_query}\b',
                rf'\binterface\s+{escaped_query}\b',
                rf'\bstruct\s+{escaped_query}\b',
                rf'\benum\s+{escaped_query}\b'
            ])
        
        elif search_type == "method":
            patterns.extend([
                rf'\b{escaped_query}\s*\(',
                rf'(public|private|protected|internal|static).*\b{escaped_query}\s*\('
            ])
        
        elif search_type == "variable":
            patterns.extend([
                rf'\b{escaped_query}\b',
                rf'(var|int|string|bool|double|float|decimal|object)\s+{escaped_query}\b'
            ])
        
        return patterns
    
    def analyze_project_structure(self) -> Dict:
        """
        Analyze the overall structure of the C# project
        
        Returns:
            Dictionary with project analysis
        """
        analysis = {
            "namespaces": set(),
            "classes": set(),
            "interfaces": set(),
            "methods": [],
            "using_statements": set(),
            "project_files": []
        }
        
        try:
            for root, dirs, files in os.walk(self.code_folder_path):
                root_path = Path(root)
                
                # Skip unwanted directories
                dirs[:] = [d for d in dirs if not self._should_skip_folder(root_path / d)]
                
                for file in files:
                    file_path = root_path / file
                    
                    if file_path.suffix.lower() == '.cs':
                        self._analyze_cs_file(file_path, analysis)
                    elif file_path.suffix.lower() in ['.csproj', '.sln']:
                        analysis["project_files"].append(str(file_path.relative_to(self.code_folder_path)))
                        
        except Exception as e:
            analysis["error"] = f"Analysis failed: {str(e)}"
        
        # Convert sets to lists for JSON serialization
        return {
            "namespaces": list(analysis["namespaces"]),
            "classes": list(analysis["classes"]),
            "interfaces": list(analysis["interfaces"]),
            "methods": analysis["methods"][:50],  # Limit to first 50 methods
            "using_statements": list(analysis["using_statements"]),
            "project_files": analysis["project_files"]
        }
    
    def _analyze_cs_file(self, file_path: Path, analysis: Dict):
        """Analyze a single C# file for structure"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Extract using statements
                if line.startswith('using ') and not line.startswith('using ('):
                    analysis["using_statements"].add(line)
                
                # Extract namespace
                namespace_match = re.match(r'namespace\s+([\w\.]+)', line)
                if namespace_match:
                    analysis["namespaces"].add(namespace_match.group(1))
                
                # Extract classes
                class_match = re.match(r'.*class\s+(\w+)', line)
                if class_match:
                    analysis["classes"].add(class_match.group(1))
                
                # Extract interfaces
                interface_match = re.match(r'.*interface\s+(\w+)', line)
                if interface_match:
                    analysis["interfaces"].add(interface_match.group(1))
                
                # Extract methods (simplified)
                method_match = re.match(r'.*(public|private|protected|internal).*\s+(\w+)\s*\(', line)
                if method_match and len(analysis["methods"]) < 100:
                    method_name = method_match.group(2)
                    if method_name not in ['if', 'for', 'while', 'switch', 'using']:
                        analysis["methods"].append({
                            "name": method_name,
                            "file": str(file_path.relative_to(self.code_folder_path))
                        })
                        
        except Exception:
            # Skip files that can't be analyzed
            pass
    
    def get_file_content(self, file_path: str, max_lines: int = 100) -> Dict:
        """
        Get content of a specific file with line numbers
        
        Args:
            file_path: Relative path to the file
            max_lines: Maximum number of lines to return
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            full_path = self.code_folder_path / file_path
            
            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            limited_lines = lines[:max_lines]
            
            numbered_lines = []
            for i, line in enumerate(limited_lines, 1):
                numbered_lines.append(f"{i:4d}: {line.rstrip()}")
            
            return {
                "file": file_path,
                "total_lines": total_lines,
                "showing_lines": len(limited_lines),
                "truncated": total_lines > max_lines,
                "content": numbered_lines,
                "raw_content": ''.join(limited_lines)
            }
            
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}


def create_code_search_tool_function(code_folder_path: str, skip_folders: List[str] = None) -> Dict:
    """
    Create the tool function definition for Azure OpenAI
    
    Args:
        code_folder_path: Path to the C# project
        skip_folders: Folders to skip during search
        
    Returns:
        Tool function definition
    """
    return {
        "type": "function",
        "function": {
            "name": "code_search",
            "description": "Search and analyze C# codebase. Can search for content, classes, methods, variables, or analyze project structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "analyze", "get_file", "scan"],
                        "description": "Action to perform: 'search' for code search, 'analyze' for project structure, 'get_file' to view specific file, 'scan' for codebase overview"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query or file path (required for search and get_file actions)"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["content", "filename", "class", "method", "variable"],
                        "description": "Type of search to perform (default: content)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 20)"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether search should be case sensitive (default: false)"
                    }
                },
                "required": ["action"]
            }
        }
    }


def execute_code_search(searcher: CSharpCodeSearcher, **kwargs) -> str:
    """
    Execute code search based on parameters
    
    Args:
        searcher: CSharpCodeSearcher instance
        **kwargs: Search parameters
        
    Returns:
        JSON string with search results
    """
    action = kwargs.get("action", "search")
    
    try:
        if action == "scan":
            result = searcher.scan_codebase()
            
        elif action == "analyze":
            result = searcher.analyze_project_structure()
            
        elif action == "search":
            query = kwargs.get("query", "")
            if not query:
                return json.dumps({"error": "Query is required for search action"})
            
            result = searcher.search_code(
                query=query,
                search_type=kwargs.get("search_type", "content"),
                case_sensitive=kwargs.get("case_sensitive", False),
                max_results=kwargs.get("max_results", 20)
            )
            
        elif action == "get_file":
            file_path = kwargs.get("query", "")
            if not file_path:
                return json.dumps({"error": "File path is required for get_file action"})
            
            result = searcher.get_file_content(file_path)
            
        else:
            result = {"error": f"Unknown action: {action}"}
            
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Code search failed: {str(e)}"})


# Example usage and testing
if __name__ == "__main__":
    # Test configuration
    test_code_path = r"C:\YourCSharpProject"  # Update this path
    test_skip_folders = ['bin', 'obj', '.vs', '.git', 'packages']
    
    print("🔍 C# Code Search Tool Test")
    print("=" * 40)
    
    # Initialize searcher
    searcher = CSharpCodeSearcher(
        code_folder_path=test_code_path,
        skip_folders=test_skip_folders
    )
    
    # Test scan
    print("📊 Testing codebase scan...")
    try:
        scan_result = searcher.scan_codebase()
        print(f"✅ Found {scan_result['total_files']} files")
        print("File types found:", list(scan_result['summary'].keys()))
    except Exception as e:
        print(f"❌ Scan failed: {e}")
    
    print("\n🔧 Tool is ready for integration!")
    print(f"📁 Configure code_folder_path to point to your C# project")
    print(f"⚙️ Customize skip_folders as needed")
