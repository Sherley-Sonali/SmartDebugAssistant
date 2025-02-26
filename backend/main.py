from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import re
import os
import json
import google.generativeai as genai
from datetime import datetime
import asyncio

app = FastAPI()
# Configure the Gemini API
def setup_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')


# Data Models
class ErrorInput(BaseModel):
    error_message: str
    code_context: Optional[str] = None
    language: str = "python"
    project_id: Optional[str] = None  # Added project_id field

class Solution(BaseModel):
    fix: str
    explanation: str
    confidence: float
    code_example: str

class LearningResource(BaseModel):
    title: str
    description: str
    url: Optional[str] = None
    resource_type: str = Field(..., description="Type of resource: article, video, tutorial, etc.")

class ErrorStatistics(BaseModel):
    frequency: Optional[int] = None
    common_contexts: Optional[List[str]] = None
    related_errors: Optional[List[str]] = None
    last_occurrence: Optional[str] = None

class ErrorResponse(BaseModel):
    error_type: str
    solutions: List[Solution]
    concepts: List[str]
    learning_resources: Optional[List[LearningResource]] = None  # Added to match return type
    statistics: Optional[ErrorStatistics] = None  # Added to match return type

# Error Patterns Database
ERROR_PATTERNS = {
    "NameError": {
        "pattern": r"name '(\w+)' is not defined",
        "solutions": [
            {
                "fix": "Define the variable before using it",
                "explanation": "This error occurs when you try to use a variable that hasn't been defined yet.",
                "confidence": 0.9,
                "code_example": """
# Wrong
print(undefined_variable)

# Correct
undefined_variable = 'some value'
print(undefined_variable)
"""
            }
        ],
        "concepts": ["variable scope", "variable declaration"]
    },
    "TypeError": {
        "pattern": r"unsupported operand type\(s\) for (\+|-|\*|\/): '(\w+)' and '(\w+)'",
        "solutions": [
            {
                "fix": "Convert variables to compatible types before operation",
                "explanation": "This error occurs when you try to perform operations on incompatible types.",
                "confidence": 0.85,
                "code_example": """
# Wrong
result = "123" + 456

# Correct
result = int("123") + 456  # If you want a number
# OR
result = "123" + str(456)  # If you want a string
"""
            }
        ],
        "concepts": ["type conversion", "operators"]
    },
    "IndexError": {
        "pattern": r"list index out of range",
        "solutions": [
            {
                "fix": "Check that the index is within the bounds of the list",
                "explanation": "This error occurs when you try to access an index that doesn't exist in the list.",
                "confidence": 0.95,
                "code_example": """
# Wrong
my_list = [1, 2, 3]
print(my_list[3])  # Index 3 doesn't exist

# Correct
my_list = [1, 2, 3]
if len(my_list) > 3:
    print(my_list[3])
else:
    print("Index out of range")
"""
            }
        ],
        "concepts": ["lists", "indexing", "bounds checking"]
    },
    "KeyError": {
        "pattern": r"KeyError: '(\w+)'",
        "solutions": [
            {
                "fix": "Check if the key exists before accessing it",
                "explanation": "This error occurs when you try to access a dictionary with a key that doesn't exist.",
                "confidence": 0.9,
                "code_example": """
# Wrong
my_dict = {'a': 1, 'b': 2}
print(my_dict['c'])

# Correct
my_dict = {'a': 1, 'b': 2}
if 'c' in my_dict:
    print(my_dict['c'])
else:
    print("Key doesn't exist")
    
# Alternative using .get()
print(my_dict.get('c', 'Key doesn\'t exist'))
"""
            }
        ],
        "concepts": ["dictionaries", "key validation", "default values"]
    },
    "SyntaxError": {
        "pattern": r"SyntaxError: invalid syntax",
        "solutions": [
            {
                "fix": "Check your code for syntax errors",
                "explanation": "This generic syntax error occurs when Python can't parse your code.",
                "confidence": 0.7,
                "code_example": """
# Common syntax errors:

# 1. Missing closing parenthesis
print("Hello"

# 2. Missing colons after if/for/while statements
if x > 5
    print(x)

# 3. Incorrect indentation
if x > 5:
print(x)
"""
            }
        ],
        "concepts": ["syntax", "code structure", "indentation"]
    },
    "IndentationError": {
        "pattern": r"IndentationError: (unexpected indent|expected an indented block)",
        "solutions": [
            {
                "fix": "Fix your code's indentation",
                "explanation": "This error occurs when your code has inconsistent indentation.",
                "confidence": 0.9,
                "code_example": """
# Wrong
if x > 5:
print("x is greater than 5")  # Missing indentation

# Correct
if x > 5:
    print("x is greater than 5")  # Properly indented
"""
            }
        ],
        "concepts": ["indentation", "code blocks", "Python syntax"]
    },
    "ImportError": {
        "pattern": r"ImportError: No module named '(\w+)'",
        "solutions": [
            {
                "fix": "Install the missing module or check the import statement",
                "explanation": "This error occurs when Python can't find the module you're trying to import.",
                "confidence": 0.85,
                "code_example": """
# Error
import non_existent_module

# Fix: Install the module
# pip install module_name

# Or check if you misspelled the module name
import os  # instead of 'Os' or 'OS'
"""
            }
        ],
        "concepts": ["imports", "modules", "package management"]
    },
    "AttributeError": {
        "pattern": r"AttributeError: '(\w+)' object has no attribute '(\w+)'",
        "solutions": [
            {
                "fix": "Check if the object has the attribute you're trying to access",
                "explanation": "This error occurs when you try to access an attribute or method that doesn't exist for that object.",
                "confidence": 0.85,
                "code_example": """
# Wrong
x = 5
x.append(10)  # integers don't have an append method

# Correct
# Check the object type first
x = 5
if hasattr(x, 'append'):
    x.append(10)
else:
    print("This object doesn't have an append method")
"""
            }
        ],
        "concepts": ["object attributes", "methods", "type checking"]
    },
    "ZeroDivisionError": {
        "pattern": r"ZeroDivisionError: division by zero",
        "solutions": [
            {
                "fix": "Check for zero before dividing",
                "explanation": "This error occurs when you try to divide by zero.",
                "confidence": 0.95,
                "code_example": """
# Wrong
x = 10 / 0

# Correct
denominator = 0
if denominator != 0:
    result = 10 / denominator
else:
    result = "Cannot divide by zero"
"""
            }
        ],
        "concepts": ["division", "error checking", "defensive programming"]
    },
    "ValueError": {
        "pattern": r"ValueError: invalid literal for int\(\) with base 10: '(\w+)'",
        "solutions": [
            {
                "fix": "Ensure the string can be converted to an integer",
                "explanation": "This error occurs when you try to convert a string to an integer, but the string doesn't represent a valid integer.",
                "confidence": 0.9,
                "code_example": """
# Wrong
int("abc")

# Correct
user_input = "abc"
try:
    number = int(user_input)
except ValueError:
    print("Input must be a valid integer")
    number = 0  # default value
"""
            }
        ],
        "concepts": ["type conversion", "input validation", "exception handling"]
    }
}

ERROR_HISTORY = {}
# async def get_learning_resources(gemini_model, error_type, concepts):
#     """
#     Use Gemini API to fetch learning resources related to the error type and concepts.
#     """
#     prompt = f"""
#     As a programming educator, recommend THREE specific learning resources for someone who encountered 
#     a {error_type} error in Python. The error involves these concepts: {', '.join(concepts)}.
    
#     For each resource, provide:
#     1. A descriptive title
#     2. A brief description of what they'll learn
#     3. The type of resource (article, video, tutorial, etc.)
    
#     Format as JSON with structure:
#     [
#         {{
#             "title": "Resource title",
#             "description": "Brief description of what they'll learn",
#             "resource_type": "article/video/tutorial/etc"
#         }},
#         ...
#     ]
    
#     Focus on high-quality, beginner-friendly resources that specifically address common mistakes.
#     """
    
#     try:
#         response = await asyncio.to_thread(
#             lambda: gemini_model.generate_content(prompt)
#         )
        
#         # Extract and parse JSON from response
#         content = response.text
#         # Sometimes Gemini might wrap the JSON in markdown code blocks
#         if "```json" in content:
#             content = content.split("```json")[1].split("```")[0].strip()
#         elif "```" in content:
#             content = content.split("```")[1].split("```")[0].strip()
            
#         resources = json.loads(content)
        
#         # Validate and convert to model
#         return [LearningResource(**resource) for resource in resources[:3]]
#     except Exception as e:
#         # Fallback resources if Gemini fails
#         return [
#             LearningResource(
#                 title=f"Understanding {error_type} in Python",
#                 description=f"Learn how to debug and prevent {error_type} errors",
#                 resource_type="article"
#             ),
#             LearningResource(
#                 title=f"Common causes of {error_type}",
#                 description=f"Explore the most frequent mistakes that lead to {error_type}",
#                 resource_type="tutorial"
#             ),
#             LearningResource(
#                 title=f"Best practices to avoid {concepts[0] if concepts else 'errors'}",
#                 description="Preventive techniques for writing more robust code",
#                 resource_type="guide"
#             )
#         ]

# async def analyze_error_patterns(gemini_model, error_type, error_message, code_context, project_id):
#     """
#     Use Gemini to analyze error patterns and provide insights
#     """
#     # Update error history
#     if project_id:
#         if project_id not in ERROR_HISTORY:
#             ERROR_HISTORY[project_id] = {}
        
#         if error_type not in ERROR_HISTORY[project_id]:
#             ERROR_HISTORY[project_id][error_type] = []
        
#         ERROR_HISTORY[project_id][error_type].append({
#             "timestamp": datetime.now().isoformat(),
#             "error_message": error_message,
#             "code_context": code_context
#         })
    
#     # Get error stats
#     stats = ErrorStatistics(
#         frequency=len(ERROR_HISTORY.get(project_id, {}).get(error_type, [])) if project_id else None,
#         last_occurrence=(
#             ERROR_HISTORY.get(project_id, {}).get(error_type, [{}])[-2].get("timestamp")
#             if project_id and len(ERROR_HISTORY.get(project_id, {}).get(error_type, [])) > 1
#             else None
#         )
#     )
    
#     # If we have enough data and a project ID, use Gemini for deeper insights
#     if project_id and stats.frequency and stats.frequency > 1:
#         error_history = ERROR_HISTORY[project_id][error_type]
        
#         prompt = f"""
#         Analyze these {len(error_history)} instances of {error_type} errors in a Python project.
        
#         Error history:
#         {json.dumps(error_history[-5:] if len(error_history) > 5 else error_history)}
        
#         Based on these patterns, answer in JSON format:
#         {{
#             "common_contexts": [list of 2-3 coding patterns or contexts where this error occurs most frequently],
#             "related_errors": [list of 2-3 other error types that might occur in similar situations]
#         }}
        
#         Be specific about the patterns you observe.
#         """
        
#         try:
#             response = await asyncio.to_thread(
#                 lambda: gemini_model.generate_content(prompt)
#             )
            
#             # Extract and parse JSON
#             content = response.text
#             if "```json" in content:
#                 content = content.split("```json")[1].split("```")[0].strip()
#             elif "```" in content:
#                 content = content.split("```")[1].split("```")[0].strip()
                
#             analysis = json.loads(content)
            
#             stats.common_contexts = analysis.get("common_contexts", [])
#             stats.related_errors = analysis.get("related_errors", [])
#         except Exception as e:
#             # Fallback if Gemini fails
#             pass
    
#     return stats

# # Main function with Gemini integration
# async def analyze_with_gemini(
#     error_input: ErrorInput,
#     error_type: str,
#     solutions: List[Solution],
#     concepts: List[str]
# ):
#     # Initialize Gemini
#     try:
#         gemini_model = setup_gemini()
        
#         # Get learning resources from Gemini
#         learning_resources = await get_learning_resources(gemini_model, error_type, concepts)
        
#         # Get error statistics and patterns
#         statistics = await analyze_error_patterns(
#             gemini_model, 
#             error_type, 
#             error_input.error_message, 
#             error_input.code_context, 
#             error_input.project_id
#         )
        
#         return ErrorResponse(
#             error_type=error_type,
#             solutions=solutions,
#             concepts=concepts,
#             learning_resources=learning_resources,
#             statistics=statistics
#         )
#     except Exception as e:
#         # Fallback if Gemini integration fails
#         return ErrorResponse(
#             error_type=error_type,
#             solutions=solutions,
#             concepts=concepts,
#             learning_resources=[
#                 LearningResource(
#                     title=f"Understanding {error_type}",
#                     description=f"Learn about common {error_type} issues",
#                     resource_type="guide"
#                 )
#             ],
#             statistics=ErrorStatistics()
#         )

# def analyze_code_context(error_type, error_message, code_context):
#     """
#     Analyze the provided code context to give more specific advice
#     based on the error type and surrounding code.
#     """
#     if not code_context:
#         return None
    
#     context_analysis = {
#         "specific_issue": None,
#         "specific_fix": None
#     }
    
#     # NameError context analysis
#     if error_type == "NameError":
#         # Look for similar variable names (potential typos)
#         lines = code_context.split('\n')
#         variable_pattern = r'\b(\w+)\b'
#         all_variables = set()
        
#         for line in lines:
#             matches = re.findall(variable_pattern, line)
#             all_variables.update(matches)
        
#         # Extract the undefined variable from the error message
#         undefined_var_match = re.search(r"name '(\w+)' is not defined", error_message)
#         if undefined_var_match:
#             undefined_var = undefined_var_match.group(1)
            
#             # Look for similar variable names using simple similarity check
#             similar_vars = []
#             for var in all_variables:
#                 # Simple string similarity check
#                 if var != undefined_var and abs(len(var) - len(undefined_var)) <= 2:
#                     # Count character differences
#                     differences = sum(1 for a, b in zip(var, undefined_var) if a != b)
#                     if differences <= 2:  # Allow up to 2 character differences
#                         similar_vars.append(var)
            
#             if similar_vars:
#                 context_analysis["specific_issue"] = f"You might have a typo in variable name '{undefined_var}'"
#                 context_analysis["specific_fix"] = f"Did you mean '{similar_vars[0]}'? Similar variables found: {', '.join(similar_vars)}"
    
#     # IndexError context analysis
#     elif error_type == "IndexError":
#         # Look for list declarations and their lengths
#         list_pattern = r'(\w+)\s*=\s*\[(.*?)\]'
#         list_matches = re.findall(list_pattern, code_context)
        
#         if list_matches:
#             for list_name, list_content in list_matches:
#                 # Rough estimate of list length
#                 items = list_content.split(',')
#                 list_length = len(items)
                
#                 index_pattern = rf'{list_name}\[(\d+)\]'
#                 index_matches = re.findall(index_pattern, code_context)
                
#                 for index_str in index_matches:
#                     index = int(index_str)
#                     if index >= list_length:
#                         context_analysis["specific_issue"] = f"Index {index} is out of range for list '{list_name}'"
#                         context_analysis["specific_fix"] = f"The list '{list_name}' appears to have {list_length} items (indices 0-{list_length-1})"
    
#     return context_analysis

# @app.post("/analyze_error", response_model=ErrorResponse)
# async def analyze_error(error_input: ErrorInput):
#     for error_type, error_info in ERROR_PATTERNS.items():
#         match = re.search(error_info["pattern"], error_input.error_message)
#         if match:
#             solutions = [Solution(**sol) for sol in error_info["solutions"]]
            
#             # If code context is provided, analyze it
#             if error_input.code_context:
#                 context_analysis = analyze_code_context(error_type, error_input.error_message, error_input.code_context)
#                 if context_analysis and context_analysis["specific_issue"]:
#                     # Add a new context-specific solution
#                     context_solution = Solution(
#                         fix=context_analysis["specific_fix"],
#                         explanation=context_analysis["specific_issue"],
#                         confidence=0.95,  # High confidence for context-specific solutions
#                         code_example="# Based on your specific code:\n" + error_input.code_context
#                     )
#                     solutions.insert(0, context_solution)  # Insert at beginning (higher priority)
            
#             # Use Gemini for enhanced response
#             return await analyze_with_gemini(
#                 error_input,
#                 error_type,
#                 solutions,
#                 error_info["concepts"]
#             )
    
    
#     raise HTTPException(status_code=404, detail="Error pattern not recognized")

# @app.get("/supported_languages")
# async def get_supported_languages():
#     return ["python", "javascript", "java", "csharp"]

async def get_learning_resources(gemini_model, error_type, concepts):
    """
    Use Gemini API to fetch learning resources related to the error type and concepts.
    """
    prompt = f"""
    As a programming educator, recommend THREE specific learning resources for someone who encountered 
    a {error_type} error in Python. The error involves these concepts: {', '.join(concepts)}.
    
    For each resource, provide:
    1. A descriptive title
    2. A brief description of what they'll learn
    3. The type of resource (article, video, tutorial, etc.)
    
    Format as JSON with structure:
    [
        {{
            "title": "Resource title",
            "description": "Brief description of what they'll learn",
            "resource_type": "article/video/tutorial/etc"
        }},
        ...
    ]
    
    Focus on high-quality, beginner-friendly resources that specifically address common mistakes.
    """
    
    try:
        response = await asyncio.to_thread(
            lambda: gemini_model.generate_content(prompt)
        )
        
        # Extract and parse JSON from response
        content = response.text
        # Sometimes Gemini might wrap the JSON in markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        resources = json.loads(content)
        
        # Validate and convert to model
        return [LearningResource(**resource) for resource in resources[:3]]
    except Exception as e:
        print(f"Error getting learning resources: {str(e)}")  # Add debugging
        # Fallback resources if Gemini fails
        return [
            LearningResource(
                title=f"Understanding {error_type} in Python",
                description=f"Learn how to debug and prevent {error_type} errors",
                resource_type="article"
            ),
            LearningResource(
                title=f"Common causes of {error_type}",
                description=f"Explore the most frequent mistakes that lead to {error_type}",
                resource_type="tutorial"
            ),
            LearningResource(
                title=f"Best practices to avoid {concepts[0] if concepts else 'errors'}",
                description="Preventive techniques for writing more robust code",
                resource_type="guide"
            )
        ]

async def analyze_error_patterns(gemini_model, error_type, error_message, code_context, project_id):
    """
    Use Gemini to analyze error patterns and provide insights
    """
    # Update error history
    if project_id:
        if project_id not in ERROR_HISTORY:
            ERROR_HISTORY[project_id] = {}
        
        if error_type not in ERROR_HISTORY[project_id]:
            ERROR_HISTORY[project_id][error_type] = []
        
        ERROR_HISTORY[project_id][error_type].append({
            "timestamp": datetime.now().isoformat(),
            "error_message": error_message,
            "code_context": code_context
        })
    
    # Get error stats
    stats = ErrorStatistics(
        frequency=len(ERROR_HISTORY.get(project_id, {}).get(error_type, [])) if project_id else None,
        last_occurrence=(
            ERROR_HISTORY.get(project_id, {}).get(error_type, [{}])[-2].get("timestamp")
            if project_id and len(ERROR_HISTORY.get(project_id, {}).get(error_type, [])) > 1
            else None
        )
    )
    
    # If we have enough data and a project ID, use Gemini for deeper insights
    if project_id and stats.frequency and stats.frequency > 1:
        error_history = ERROR_HISTORY[project_id][error_type]
        
        prompt = f"""
        Analyze these {len(error_history)} instances of {error_type} errors in a Python project.
        
        Error history:
        {json.dumps(error_history[-5:] if len(error_history) > 5 else error_history)}
        
        Based on these patterns, answer in JSON format:
        {{
            "common_contexts": [list of 2-3 coding patterns or contexts where this error occurs most frequently],
            "related_errors": [list of 2-3 other error types that might occur in similar situations]
        }}
        
        Be specific about the patterns you observe.
        """
        
        try:
            response = await asyncio.to_thread(
                lambda: gemini_model.generate_content(prompt)
            )
            
            # Extract and parse JSON
            content = response.text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            analysis = json.loads(content)
            
            stats.common_contexts = analysis.get("common_contexts", [])
            stats.related_errors = analysis.get("related_errors", [])
        except Exception as e:
            print(f"Error analyzing patterns: {str(e)}")  # Add debugging
            # Fallback if Gemini fails
            pass
    
    return stats

# Main function with Gemini integration
async def analyze_with_gemini(
    error_input: ErrorInput,
    error_type: str,
    solutions: List[Solution],
    concepts: List[str]
):
    # Initialize Gemini
    try:
        gemini_model = setup_gemini()
        
        # Get learning resources from Gemini
        learning_resources = await get_learning_resources(gemini_model, error_type, concepts)
        
        # Get error statistics and patterns
        statistics = await analyze_error_patterns(
            gemini_model, 
            error_type, 
            error_input.error_message, 
            error_input.code_context, 
            error_input.project_id
        )
        
        return ErrorResponse(
            error_type=error_type,
            solutions=solutions,
            concepts=concepts,
            learning_resources=learning_resources,
            statistics=statistics
        )
    except Exception as e:
        print(f"Gemini integration error: {str(e)}")  # Add debugging
        # Fallback if Gemini integration fails
        return ErrorResponse(
            error_type=error_type,
            solutions=solutions,
            concepts=concepts,
            learning_resources=[
                LearningResource(
                    title=f"Understanding {error_type}",
                    description=f"Learn about common {error_type} issues",
                    resource_type="guide"
                )
            ],
            statistics=ErrorStatistics()
        )

def analyze_code_context(error_type, error_message, code_context):
    """
    Analyze the provided code context to give more specific advice
    based on the error type and surrounding code.
    """
    if not code_context:
        return None
    
    context_analysis = {
        "specific_issue": None,
        "specific_fix": None
    }
    
    # NameError context analysis
    if error_type == "NameError":
        # Look for similar variable names (potential typos)
        lines = code_context.split('\n')
        variable_pattern = r'\b(\w+)\b'
        all_variables = set()
        
        for line in lines:
            matches = re.findall(variable_pattern, line)
            all_variables.update(matches)
        
        # Extract the undefined variable from the error message
        undefined_var_match = re.search(r"name '(\w+)' is not defined", error_message)
        if undefined_var_match:
            undefined_var = undefined_var_match.group(1)
            
            # Look for similar variable names using simple similarity check
            similar_vars = []
            for var in all_variables:
                # Simple string similarity check
                if var != undefined_var and abs(len(var) - len(undefined_var)) <= 2:
                    # Count character differences
                    differences = sum(1 for a, b in zip(var, undefined_var) if a != b)
                    if differences <= 2:  # Allow up to 2 character differences
                        similar_vars.append(var)
            
            if similar_vars:
                context_analysis["specific_issue"] = f"You might have a typo in variable name '{undefined_var}'"
                context_analysis["specific_fix"] = f"Did you mean '{similar_vars[0]}'? Similar variables found: {', '.join(similar_vars)}"
    
    # IndexError context analysis
    elif error_type == "IndexError":
        # Look for list declarations and their lengths
        list_pattern = r'(\w+)\s*=\s*\[(.*?)\]'
        list_matches = re.findall(list_pattern, code_context)
        
        if list_matches:
            for list_name, list_content in list_matches:
                # Rough estimate of list length
                items = list_content.split(',')
                list_length = len(items)
                
                index_pattern = rf'{list_name}\[(\d+)\]'
                index_matches = re.findall(index_pattern, code_context)
                
                for index_str in index_matches:
                    index = int(index_str)
                    if index >= list_length:
                        context_analysis["specific_issue"] = f"Index {index} is out of range for list '{list_name}'"
                        context_analysis["specific_fix"] = f"The list '{list_name}' appears to have {list_length} items (indices 0-{list_length-1})"
    
    return context_analysis

@app.post("/analyze_error", response_model=ErrorResponse)
async def analyze_error(error_input: ErrorInput):
    for error_type, error_info in ERROR_PATTERNS.items():
        match = re.search(error_info["pattern"], error_input.error_message)
        if match:
            solutions = [Solution(**sol) for sol in error_info["solutions"]]
            
            # If code context is provided, analyze it
            if error_input.code_context:
                context_analysis = analyze_code_context(error_type, error_input.error_message, error_input.code_context)
                if context_analysis and context_analysis["specific_issue"]:
                    # Add a new context-specific solution
                    context_solution = Solution(
                        fix=context_analysis["specific_fix"],
                        explanation=context_analysis["specific_issue"],
                        confidence=0.95,  # High confidence for context-specific solutions
                        code_example="# Based on your specific code:\n" + error_input.code_context
                    )
                    solutions.insert(0, context_solution)  # Insert at beginning (higher priority)
            
            # Use Gemini for enhanced response
            return await analyze_with_gemini(
                error_input,
                error_type,
                solutions,
                error_info["concepts"]
            )
    
    # If no pattern matches, try using Gemini to analyze the unknown error
    try:
        gemini_model = setup_gemini()
        
        prompt = f"""
        Analyze this Python error message that doesn't match our standard patterns:
        
        Error message: {error_input.error_message}
        
        {f"Code context: {error_input.code_context}" if error_input.code_context else ""}
        
        Provide a JSON response with:
        {{
            "error_type": "The likely error type",
            "solutions": [
                {{
                    "fix": "Suggested fix",
                    "explanation": "Why this error happens",
                    "confidence": 0.7,
                    "code_example": "Example code showing the fix"
                }}
            ],
            "concepts": ["concept1", "concept2"]
        }}
        """
        
        response = await asyncio.to_thread(
            lambda: gemini_model.generate_content(prompt)
        )
        
        # Extract and parse JSON
        content = response.text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        analysis = json.loads(content)
        
        # Convert to our model objects
        error_type = analysis.get("error_type", "Unknown Error")
        solutions = [Solution(**sol) for sol in analysis.get("solutions", [])]
        concepts = analysis.get("concepts", [])
        
        # Get more detailed information using our standard flow
        return await analyze_with_gemini(
            error_input,
            error_type,
            solutions,
            concepts
        )
        
    except Exception as e:
        print(f"Failed to analyze unknown error: {str(e)}")
        # If Gemini integration fails, return a generic error response
        raise HTTPException(status_code=404, detail="Error pattern not recognized and failed to analyze with Gemini")

@app.get("/supported_languages")
async def get_supported_languages():
    return ["python", "javascript", "java", "csharp"]


# Enable CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)