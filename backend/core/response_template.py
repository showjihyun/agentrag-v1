"""
Response Template Manager for structured LLM outputs.

Provides templates for consistent, structured responses:
- Direct answer format
- Detailed explanation format
- Source citation format
- Confidence reporting
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ResponseFormat(Enum):
    """Response format types"""
    CONCISE = "concise"  # 1-2 sentences
    STANDARD = "standard"  # Direct answer + explanation
    DETAILED = "detailed"  # Comprehensive with sources
    STRUCTURED = "structured"  # JSON-like structured output


@dataclass
class ResponseTemplate:
    """Template for structured response"""
    format_type: ResponseFormat
    template: str
    max_tokens: int
    temperature: float


class ResponseTemplateManager:
    """
    Manages response templates for consistent LLM outputs.
    
    Features:
    - Predefined templates for different response types
    - Structured output format
    - Automatic source citation
    - Confidence reporting
    """
    
    # Response templates with clear structure
    TEMPLATES = {
        ResponseFormat.CONCISE: ResponseTemplate(
            format_type=ResponseFormat.CONCISE,
            template="""Answer in 1-2 sentences based on provided sources.

Format:
[Direct answer with source citation]

Example:
According to web search, Donald Trump is the current US president. [Source: Web]""",
            max_tokens=100,
            temperature=0.3
        ),
        
        ResponseFormat.STANDARD: ResponseTemplate(
            format_type=ResponseFormat.STANDARD,
            template="""Provide a structured answer with the following format:

## Direct Answer
[1-2 sentence direct answer with source]

## Explanation
[2-3 sentences providing context and details]

## Sources
- [Source type]: [Title/Description]

## Confidence
[High/Medium/Low] - [Brief reason]

Example:
## Direct Answer
According to recent web search, Donald Trump is the current US president. [Source: Web]

## Explanation
This information comes from multiple recent web sources dated 2024. The web search results consistently report this across different news outlets.

## Sources
- Web: "Trump Presidency 2024" - news.example.com
- Internal: Company policy document

## Confidence
High - Multiple recent web sources confirm this information.""",
            max_tokens=300,
            temperature=0.5
        ),
        
        ResponseFormat.DETAILED: ResponseTemplate(
            format_type=ResponseFormat.DETAILED,
            template="""Provide a comprehensive structured answer:

## Direct Answer (1-2 sentences)
[Concise answer with primary source]

## Detailed Explanation (2-3 paragraphs)
[Comprehensive explanation with context]
[Supporting details and analysis]
[Implications or additional insights]

## Sources
### Web Search Results
- [Title] - [URL] - [Relevance note]

### Internal Documents
- [Document name] - [Relevance note]

## Confidence Assessment
**Level**: [High/Medium/Low]
**Reasoning**: [Detailed explanation of confidence level]
**Limitations**: [Any caveats or missing information]

## Related Information
[Optional: Related topics or follow-up suggestions]""",
            max_tokens=500,
            temperature=0.7
        ),
        
        ResponseFormat.STRUCTURED: ResponseTemplate(
            format_type=ResponseFormat.STRUCTURED,
            template="""Provide a JSON-structured response:

{
  "direct_answer": "[1-2 sentence answer]",
  "explanation": "[Detailed explanation]",
  "sources": [
    {
      "type": "web|internal",
      "title": "[Source title]",
      "url": "[URL if web]",
      "relevance": "[Why this source is relevant]"
    }
  ],
  "confidence": {
    "level": "high|medium|low",
    "score": 0.0-1.0,
    "reasoning": "[Why this confidence level]"
  },
  "key_points": [
    "[Key point 1]",
    "[Key point 2]"
  ]
}""",
            max_tokens=400,
            temperature=0.3
        )
    }
    
    def __init__(self):
        """Initialize ResponseTemplateManager"""
        logger.info("ResponseTemplateManager initialized")
    
    def get_template(
        self,
        format_type: ResponseFormat = ResponseFormat.STANDARD
    ) -> ResponseTemplate:
        """
        Get response template by format type.
        
        Args:
            format_type: Type of response format
            
        Returns:
            ResponseTemplate
        """
        return self.TEMPLATES.get(format_type, self.TEMPLATES[ResponseFormat.STANDARD])
    
    def build_prompt_with_template(
        self,
        query: str,
        context: str,
        format_type: ResponseFormat = ResponseFormat.STANDARD,
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Build prompt with response template.
        
        Args:
            query: User query
            context: Context (RAG + Web results)
            format_type: Response format type
            custom_instructions: Optional custom instructions
            
        Returns:
            Formatted prompt with template
        """
        template = self.get_template(format_type)
        
        prompt_parts = [
            f"Query: {query}",
            "",
            "Context:",
            context,
            "",
            "Response Format (REQUIRED):",
            template.template
        ]
        
        if custom_instructions:
            prompt_parts.extend([
                "",
                "Additional Instructions:",
                custom_instructions
            ])
        
        return "\n".join(prompt_parts)
    
    def validate_response(
        self,
        response: str,
        format_type: ResponseFormat
    ) -> Dict[str, Any]:
        """
        Validate if response follows the template.
        
        Args:
            response: Generated response
            format_type: Expected format type
            
        Returns:
            Validation result with score and issues
        """
        issues = []
        score = 1.0
        
        if format_type == ResponseFormat.STANDARD:
            # Check for required sections
            required_sections = ["## Direct Answer", "## Explanation", "## Sources", "## Confidence"]
            
            for section in required_sections:
                if section not in response:
                    issues.append(f"Missing section: {section}")
                    score -= 0.25
        
        elif format_type == ResponseFormat.DETAILED:
            required_sections = [
                "## Direct Answer",
                "## Detailed Explanation",
                "## Sources",
                "## Confidence Assessment"
            ]
            
            for section in required_sections:
                if section not in response:
                    issues.append(f"Missing section: {section}")
                    score -= 0.2
        
        elif format_type == ResponseFormat.STRUCTURED:
            # Check for JSON structure
            if not (response.strip().startswith("{") and response.strip().endswith("}")):
                issues.append("Response is not valid JSON structure")
                score = 0.0
        
        # Check for source citations
        if "[Source:" not in response and "Sources" not in response:
            issues.append("No source citations found")
            score -= 0.1
        
        score = max(0.0, min(1.0, score))
        
        return {
            "valid": score >= 0.7,
            "score": score,
            "issues": issues
        }
    
    def extract_structured_data(
        self,
        response: str,
        format_type: ResponseFormat
    ) -> Dict[str, Any]:
        """
        Extract structured data from response.
        
        Args:
            response: Generated response
            format_type: Response format type
            
        Returns:
            Extracted structured data
        """
        data = {
            "raw_response": response,
            "format_type": format_type.value
        }
        
        if format_type == ResponseFormat.STANDARD or format_type == ResponseFormat.DETAILED:
            # Extract sections
            sections = {}
            current_section = None
            current_content = []
            
            for line in response.split("\n"):
                if line.startswith("## "):
                    # Save previous section
                    if current_section:
                        sections[current_section] = "\n".join(current_content).strip()
                    
                    # Start new section
                    current_section = line[3:].strip()
                    current_content = []
                else:
                    current_content.append(line)
            
            # Save last section
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            
            data["sections"] = sections
            data["direct_answer"] = sections.get("Direct Answer", "")
            data["explanation"] = sections.get("Explanation", "") or sections.get("Detailed Explanation", "")
            data["sources"] = sections.get("Sources", "")
            data["confidence"] = sections.get("Confidence", "") or sections.get("Confidence Assessment", "")
        
        elif format_type == ResponseFormat.STRUCTURED:
            # Parse JSON
            import json
            try:
                data["structured"] = json.loads(response)
            except json.JSONDecodeError:
                data["structured"] = None
                data["parse_error"] = "Invalid JSON"
        
        return data


# Singleton instance
_response_template_manager: Optional[ResponseTemplateManager] = None


def get_response_template_manager() -> ResponseTemplateManager:
    """
    Get or create global ResponseTemplateManager instance.
    
    Returns:
        ResponseTemplateManager instance
    """
    global _response_template_manager
    
    if _response_template_manager is None:
        _response_template_manager = ResponseTemplateManager()
    
    return _response_template_manager
