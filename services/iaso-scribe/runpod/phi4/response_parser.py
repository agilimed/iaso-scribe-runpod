"""
Response Parser for Phi-4 Tagged Outputs
Handles separation of reasoning and solution sections for frontend display
"""

import re
from typing import Dict, Optional, Tuple

class Phi4ResponseParser:
    """Parser for Phi-4 responses with think/solution tags"""
    
    THINK_PATTERN = re.compile(r'<think>(.*?)</think>', re.DOTALL)
    SOLUTION_PATTERN = re.compile(r'<solution>(.*?)</solution>', re.DOTALL)
    
    @classmethod
    def parse(cls, response: str) -> Dict[str, any]:
        """
        Parse a Phi-4 response to extract reasoning and solution sections.
        
        Args:
            response: Raw response from Phi-4 model
            
        Returns:
            Dict with:
                - reasoning: Content from <think> tags
                - solution: Content from <solution> tags  
                - has_tags: Whether both tags were found
                - raw: Original response
        """
        think_match = cls.THINK_PATTERN.search(response)
        solution_match = cls.SOLUTION_PATTERN.search(response)
        
        return {
            "reasoning": think_match.group(1).strip() if think_match else "",
            "solution": solution_match.group(1).strip() if solution_match else response.strip(),
            "has_tags": bool(think_match and solution_match),
            "raw": response
        }
    
    @classmethod
    def parse_streaming(cls, chunk: str, buffer: str = "") -> Tuple[Optional[str], Optional[str], str]:
        """
        Parse streaming chunks, detecting when tags complete.
        
        Args:
            chunk: New chunk of text
            buffer: Accumulated buffer from previous chunks
            
        Returns:
            Tuple of (reasoning_if_complete, solution_if_complete, updated_buffer)
        """
        buffer += chunk
        reasoning_complete = None
        solution_complete = None
        
        # Check if we have a complete <think> section
        if "</think>" in buffer and "<think>" in buffer:
            match = cls.THINK_PATTERN.search(buffer)
            if match:
                reasoning_complete = match.group(1).strip()
                # Remove the completed think section from buffer
                buffer = buffer.replace(match.group(0), "", 1)
        
        # Check if we have a complete <solution> section
        if "</solution>" in buffer and "<solution>" in buffer:
            match = cls.SOLUTION_PATTERN.search(buffer)
            if match:
                solution_complete = match.group(1).strip()
                # Remove the completed solution section from buffer
                buffer = buffer.replace(match.group(0), "", 1)
        
        return reasoning_complete, solution_complete, buffer
    
    @classmethod
    def format_for_display(cls, parsed_response: Dict[str, any], format_type: str = "text") -> str:
        """
        Format parsed response for display.
        
        Args:
            parsed_response: Output from parse() method
            format_type: "text", "markdown", or "html"
            
        Returns:
            Formatted string for display
        """
        if not parsed_response["has_tags"]:
            return parsed_response["raw"]
        
        if format_type == "markdown":
            output = ""
            if parsed_response["reasoning"]:
                output += "## 🧠 Clinical Reasoning\n\n"
                output += parsed_response["reasoning"] + "\n\n"
            if parsed_response["solution"]:
                output += "## 📋 Clinical Summary\n\n" 
                output += parsed_response["solution"]
            return output
            
        elif format_type == "html":
            output = ""
            if parsed_response["reasoning"]:
                output += '<div class="reasoning-section">\n'
                output += '<h3>🧠 Clinical Reasoning</h3>\n'
                output += f'<div class="reasoning-content">{parsed_response["reasoning"]}</div>\n'
                output += '</div>\n'
            if parsed_response["solution"]:
                output += '<div class="solution-section">\n'
                output += '<h3>📋 Clinical Summary</h3>\n'
                output += f'<div class="solution-content">{parsed_response["solution"]}</div>\n'
                output += '</div>\n'
            return output
            
        else:  # text format
            output = ""
            if parsed_response["reasoning"]:
                output += "=== CLINICAL REASONING ===\n\n"
                output += parsed_response["reasoning"] + "\n\n"
            if parsed_response["solution"]:
                output += "=== CLINICAL SUMMARY ===\n\n"
                output += parsed_response["solution"]
            return output

# Example usage for frontend integration
"""
# For non-streaming response:
parser = Phi4ResponseParser()
response = model_output["insights"]
parsed = parser.parse(response)

# Display in UI
if parsed["has_tags"]:
    show_reasoning_section(parsed["reasoning"])
    show_solution_section(parsed["solution"])
else:
    show_full_response(parsed["raw"])

# For streaming response:
buffer = ""
for chunk in stream:
    reasoning, solution, buffer = parser.parse_streaming(chunk, buffer)
    if reasoning:
        update_reasoning_display(reasoning)
    if solution:
        update_solution_display(solution)
"""