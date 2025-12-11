"""
Agent Template System

Provides pre-defined agent templates for quick agent creation:
- Customer Support Agent
- Research Assistant
- Data Analyst
- Code Assistant
- Content Writer
- Sales Assistant
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import uuid


class AgentCategory(str, Enum):
    """Agent template categories."""
    CUSTOMER_SUPPORT = "customer_support"
    RESEARCH = "research"
    DATA_ANALYSIS = "data_analysis"
    DEVELOPMENT = "development"
    CONTENT = "content"
    SALES = "sales"
    PRODUCTIVITY = "productivity"
    CUSTOM = "custom"


class AgentComplexity(str, Enum):
    """Agent complexity levels."""
    SIMPLE = "simple"      # Single tool, basic prompt
    MODERATE = "moderate"  # Multiple tools, structured prompt
    ADVANCED = "advanced"  # Complex workflow, RAG integration


@dataclass
class ToolConfig:
    """Tool configuration for agent template."""
    tool_id: str
    name: str
    description: str
    required: bool = True
    default_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTemplate:
    """Agent template definition."""
    id: str
    name: str
    description: str
    category: AgentCategory
    complexity: AgentComplexity
    icon: str
    
    # LLM Configuration
    recommended_provider: str = "openai"
    recommended_model: str = "gpt-4"
    fallback_models: List[str] = field(default_factory=list)
    
    # Prompt Configuration
    system_prompt: str = ""
    example_prompts: List[str] = field(default_factory=list)
    
    # Tool Configuration
    tools: List[ToolConfig] = field(default_factory=list)
    
    # Knowledge Base Configuration
    requires_knowledgebase: bool = False
    knowledgebase_description: str = ""
    
    # Advanced Configuration
    temperature: float = 0.7
    max_tokens: int = 2048
    enable_memory: bool = True
    enable_streaming: bool = True
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["category"] = self.category.value
        data["complexity"] = self.complexity.value
        data["tools"] = [asdict(t) for t in self.tools]
        return data


# ============================================================================
# Pre-defined Agent Templates
# ============================================================================

AGENT_TEMPLATES: Dict[str, AgentTemplate] = {}


def register_template(template: AgentTemplate) -> None:
    """Register an agent template."""
    AGENT_TEMPLATES[template.id] = template


# Customer Support Agent
register_template(AgentTemplate(
    id="customer_support_basic",
    name="Customer Support Agent",
    description="AI agent for handling customer inquiries, FAQs, and support tickets with empathy and efficiency.",
    category=AgentCategory.CUSTOMER_SUPPORT,
    complexity=AgentComplexity.MODERATE,
    icon="headphones",
    recommended_provider="openai",
    recommended_model="gpt-4",
    fallback_models=["gpt-3.5-turbo", "claude-3-sonnet"],
    system_prompt="""You are a helpful and empathetic customer support agent. Your role is to:

1. Listen carefully to customer concerns
2. Provide accurate and helpful information
3. Resolve issues efficiently while maintaining a friendly tone
4. Escalate complex issues when necessary
5. Follow up to ensure customer satisfaction

Guidelines:
- Always greet customers warmly
- Acknowledge their concerns before providing solutions
- Use clear, simple language
- Offer alternatives when the primary solution isn't available
- End conversations with a positive note and offer further assistance

If you don't know the answer, be honest and offer to find out or escalate to a human agent.""",
    example_prompts=[
        "I haven't received my order yet. Can you help?",
        "How do I reset my password?",
        "I'd like to request a refund for my recent purchase.",
        "What are your business hours?",
    ],
    tools=[
        ToolConfig(
            tool_id="vector_search",
            name="Knowledge Base Search",
            description="Search company knowledge base for answers",
            required=True,
            default_config={"top_k": 5}
        ),
        ToolConfig(
            tool_id="http_request",
            name="Order Lookup",
            description="Look up order status",
            required=False,
            default_config={}
        ),
    ],
    requires_knowledgebase=True,
    knowledgebase_description="Upload FAQs, product documentation, and support policies",
    temperature=0.5,
    max_tokens=1024,
    enable_memory=True,
    tags=["customer-service", "support", "faq"],
    use_cases=[
        "Answering frequently asked questions",
        "Order status inquiries",
        "Product information requests",
        "Basic troubleshooting",
    ],
))


# Research Assistant
register_template(AgentTemplate(
    id="research_assistant",
    name="Research Assistant",
    description="AI agent for conducting research, summarizing information, and providing insights from multiple sources.",
    category=AgentCategory.RESEARCH,
    complexity=AgentComplexity.ADVANCED,
    icon="search",
    recommended_provider="openai",
    recommended_model="gpt-4",
    fallback_models=["claude-3-opus", "gpt-4-turbo"],
    system_prompt="""You are an expert research assistant. Your role is to:

1. Understand research queries thoroughly
2. Search and analyze information from multiple sources
3. Synthesize findings into clear, structured summaries
4. Cite sources and provide references
5. Identify gaps in information and suggest further research

Research Methodology:
- Start with broad searches, then narrow down
- Cross-reference information from multiple sources
- Distinguish between facts, opinions, and speculation
- Present balanced viewpoints on controversial topics
- Highlight key findings and actionable insights

Output Format:
- Executive Summary
- Key Findings
- Detailed Analysis
- Sources and References
- Recommendations for Further Research""",
    example_prompts=[
        "Research the latest trends in renewable energy technology",
        "Summarize the key findings from recent AI safety research",
        "Compare different approaches to sustainable agriculture",
        "What are the pros and cons of remote work policies?",
    ],
    tools=[
        ToolConfig(
            tool_id="web_search",
            name="Web Search",
            description="Search the web for information",
            required=True,
            default_config={"max_results": 10}
        ),
        ToolConfig(
            tool_id="vector_search",
            name="Document Search",
            description="Search uploaded documents",
            required=True,
            default_config={"top_k": 10}
        ),
        ToolConfig(
            tool_id="python_code",
            name="Data Analysis",
            description="Analyze and visualize data",
            required=False,
            default_config={}
        ),
    ],
    requires_knowledgebase=True,
    knowledgebase_description="Upload research papers, reports, and reference documents",
    temperature=0.3,
    max_tokens=4096,
    enable_memory=True,
    tags=["research", "analysis", "summarization"],
    use_cases=[
        "Literature reviews",
        "Market research",
        "Competitive analysis",
        "Trend analysis",
    ],
))


# Data Analyst Agent
register_template(AgentTemplate(
    id="data_analyst",
    name="Data Analyst Agent",
    description="AI agent for analyzing data, generating insights, and creating visualizations.",
    category=AgentCategory.DATA_ANALYSIS,
    complexity=AgentComplexity.ADVANCED,
    icon="bar-chart",
    recommended_provider="openai",
    recommended_model="gpt-4",
    fallback_models=["gpt-4-turbo", "claude-3-opus"],
    system_prompt="""You are an expert data analyst. Your role is to:

1. Understand data analysis requirements
2. Write and execute code to analyze data
3. Generate meaningful insights and visualizations
4. Explain findings in clear, non-technical language
5. Recommend data-driven actions

Analysis Approach:
- Start with exploratory data analysis (EDA)
- Identify patterns, trends, and anomalies
- Use appropriate statistical methods
- Create clear visualizations
- Validate findings before presenting

When writing code:
- Use pandas for data manipulation
- Use matplotlib/seaborn for visualizations
- Handle missing data appropriately
- Comment your code for clarity
- Always validate results""",
    example_prompts=[
        "Analyze the sales data and identify top-performing products",
        "Create a visualization showing monthly revenue trends",
        "Find correlations between customer demographics and purchase behavior",
        "Generate a summary report of key metrics",
    ],
    tools=[
        ToolConfig(
            tool_id="python_code",
            name="Python Executor",
            description="Execute Python code for data analysis",
            required=True,
            default_config={"timeout": 60}
        ),
        ToolConfig(
            tool_id="database_query",
            name="Database Query",
            description="Query databases for data",
            required=False,
            default_config={}
        ),
        ToolConfig(
            tool_id="csv_parser",
            name="CSV Parser",
            description="Parse and process CSV files",
            required=False,
            default_config={}
        ),
    ],
    requires_knowledgebase=False,
    temperature=0.2,
    max_tokens=4096,
    enable_memory=True,
    tags=["data", "analytics", "visualization", "python"],
    use_cases=[
        "Sales analysis",
        "Customer segmentation",
        "Performance reporting",
        "Trend forecasting",
    ],
))


# Code Assistant
register_template(AgentTemplate(
    id="code_assistant",
    name="Code Assistant",
    description="AI agent for helping with coding tasks, debugging, and code reviews.",
    category=AgentCategory.DEVELOPMENT,
    complexity=AgentComplexity.MODERATE,
    icon="code",
    recommended_provider="openai",
    recommended_model="gpt-4",
    fallback_models=["gpt-4-turbo", "claude-3-opus"],
    system_prompt="""You are an expert software developer and code assistant. Your role is to:

1. Help write clean, efficient, and well-documented code
2. Debug issues and explain error messages
3. Review code and suggest improvements
4. Explain programming concepts clearly
5. Follow best practices and coding standards

Coding Guidelines:
- Write readable, maintainable code
- Follow language-specific conventions
- Include appropriate error handling
- Add comments for complex logic
- Consider performance implications
- Write unit tests when appropriate

When reviewing code:
- Check for bugs and edge cases
- Suggest performance optimizations
- Identify security vulnerabilities
- Recommend better patterns or approaches
- Explain the reasoning behind suggestions""",
    example_prompts=[
        "Help me write a function to parse JSON data in Python",
        "Debug this error: TypeError: Cannot read property 'map' of undefined",
        "Review this code and suggest improvements",
        "Explain how async/await works in JavaScript",
    ],
    tools=[
        ToolConfig(
            tool_id="python_code",
            name="Code Executor",
            description="Execute and test code",
            required=True,
            default_config={"timeout": 30}
        ),
        ToolConfig(
            tool_id="web_search",
            name="Documentation Search",
            description="Search for documentation and examples",
            required=False,
            default_config={}
        ),
    ],
    requires_knowledgebase=False,
    temperature=0.3,
    max_tokens=4096,
    enable_memory=True,
    tags=["coding", "development", "debugging", "review"],
    use_cases=[
        "Code generation",
        "Bug fixing",
        "Code review",
        "Learning programming",
    ],
))


# Content Writer
register_template(AgentTemplate(
    id="content_writer",
    name="Content Writer",
    description="AI agent for creating engaging content including articles, blog posts, and marketing copy.",
    category=AgentCategory.CONTENT,
    complexity=AgentComplexity.MODERATE,
    icon="edit",
    recommended_provider="openai",
    recommended_model="gpt-4",
    fallback_models=["gpt-4-turbo", "claude-3-sonnet"],
    system_prompt="""You are a skilled content writer. Your role is to:

1. Create engaging, well-structured content
2. Adapt tone and style to the target audience
3. Optimize content for readability and SEO
4. Maintain brand voice consistency
5. Edit and improve existing content

Writing Guidelines:
- Start with a compelling hook
- Use clear, concise language
- Break content into scannable sections
- Include relevant examples and data
- End with a strong call-to-action

Content Types:
- Blog posts and articles
- Marketing copy
- Social media content
- Email newsletters
- Product descriptions

Always ask for:
- Target audience
- Desired tone (professional, casual, etc.)
- Key messages to convey
- Any specific requirements or constraints""",
    example_prompts=[
        "Write a blog post about the benefits of remote work",
        "Create social media posts for our new product launch",
        "Help me improve this email newsletter",
        "Write a compelling product description for our software",
    ],
    tools=[
        ToolConfig(
            tool_id="web_search",
            name="Research",
            description="Research topics for content",
            required=False,
            default_config={}
        ),
    ],
    requires_knowledgebase=True,
    knowledgebase_description="Upload brand guidelines, style guides, and reference content",
    temperature=0.7,
    max_tokens=4096,
    enable_memory=True,
    tags=["writing", "content", "marketing", "copywriting"],
    use_cases=[
        "Blog writing",
        "Marketing copy",
        "Social media content",
        "Email campaigns",
    ],
))


# Sales Assistant
register_template(AgentTemplate(
    id="sales_assistant",
    name="Sales Assistant",
    description="AI agent for supporting sales activities including lead qualification, product recommendations, and follow-ups.",
    category=AgentCategory.SALES,
    complexity=AgentComplexity.MODERATE,
    icon="dollar-sign",
    recommended_provider="openai",
    recommended_model="gpt-4",
    fallback_models=["gpt-3.5-turbo", "claude-3-sonnet"],
    system_prompt="""You are a professional sales assistant. Your role is to:

1. Qualify leads and understand customer needs
2. Recommend appropriate products or services
3. Handle objections professionally
4. Provide accurate pricing and availability information
5. Schedule follow-ups and demos

Sales Approach:
- Build rapport before selling
- Ask discovery questions to understand needs
- Focus on value and benefits, not just features
- Address concerns with empathy
- Create urgency without being pushy

Key Questions to Ask:
- What challenges are you trying to solve?
- What's your timeline for implementation?
- Who else is involved in the decision?
- What's your budget range?
- Have you considered other solutions?

Always maintain professionalism and never make promises you can't keep.""",
    example_prompts=[
        "A prospect is interested in our enterprise plan. What questions should I ask?",
        "How should I respond to 'Your product is too expensive'?",
        "Help me write a follow-up email after a demo",
        "What are the key differentiators of our product?",
    ],
    tools=[
        ToolConfig(
            tool_id="vector_search",
            name="Product Knowledge",
            description="Search product information",
            required=True,
            default_config={"top_k": 5}
        ),
        ToolConfig(
            tool_id="http_request",
            name="CRM Integration",
            description="Access CRM data",
            required=False,
            default_config={}
        ),
    ],
    requires_knowledgebase=True,
    knowledgebase_description="Upload product catalogs, pricing sheets, and sales playbooks",
    temperature=0.6,
    max_tokens=2048,
    enable_memory=True,
    tags=["sales", "crm", "lead-qualification"],
    use_cases=[
        "Lead qualification",
        "Product recommendations",
        "Objection handling",
        "Follow-up automation",
    ],
))


# Meeting Assistant
register_template(AgentTemplate(
    id="meeting_assistant",
    name="Meeting Assistant",
    description="AI agent for managing meetings, taking notes, and generating action items.",
    category=AgentCategory.PRODUCTIVITY,
    complexity=AgentComplexity.SIMPLE,
    icon="calendar",
    recommended_provider="openai",
    recommended_model="gpt-4",
    fallback_models=["gpt-3.5-turbo", "claude-3-sonnet"],
    system_prompt="""You are a professional meeting assistant. Your role is to:

1. Help prepare meeting agendas
2. Take structured meeting notes
3. Identify and track action items
4. Summarize key decisions and discussions
5. Send follow-up communications

Meeting Notes Format:
- Date and attendees
- Agenda items covered
- Key discussion points
- Decisions made
- Action items (with owners and deadlines)
- Next steps

Best Practices:
- Capture key points, not verbatim transcripts
- Highlight decisions and commitments
- Assign clear ownership for action items
- Include relevant context for absent stakeholders
- Follow up on previous action items""",
    example_prompts=[
        "Create an agenda for our weekly team meeting",
        "Summarize these meeting notes and extract action items",
        "Draft a follow-up email with meeting highlights",
        "What were the key decisions from last week's meeting?",
    ],
    tools=[],
    requires_knowledgebase=False,
    temperature=0.4,
    max_tokens=2048,
    enable_memory=True,
    tags=["meetings", "productivity", "notes"],
    use_cases=[
        "Meeting preparation",
        "Note taking",
        "Action item tracking",
        "Follow-up emails",
    ],
))


# ============================================================================
# Template Service
# ============================================================================

class AgentTemplateService:
    """Service for managing agent templates."""
    
    @staticmethod
    def get_all_templates() -> List[Dict[str, Any]]:
        """Get all available templates."""
        return [t.to_dict() for t in AGENT_TEMPLATES.values()]
    
    @staticmethod
    def get_template(template_id: str) -> Optional[AgentTemplate]:
        """Get a specific template by ID."""
        return AGENT_TEMPLATES.get(template_id)
    
    @staticmethod
    def get_templates_by_category(category: AgentCategory) -> List[Dict[str, Any]]:
        """Get templates by category."""
        return [
            t.to_dict() for t in AGENT_TEMPLATES.values()
            if t.category == category
        ]
    
    @staticmethod
    def get_templates_by_complexity(complexity: AgentComplexity) -> List[Dict[str, Any]]:
        """Get templates by complexity level."""
        return [
            t.to_dict() for t in AGENT_TEMPLATES.values()
            if t.complexity == complexity
        ]
    
    @staticmethod
    def search_templates(query: str) -> List[Dict[str, Any]]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        results = []
        
        for template in AGENT_TEMPLATES.values():
            if (
                query_lower in template.name.lower() or
                query_lower in template.description.lower() or
                any(query_lower in tag for tag in template.tags)
            ):
                results.append(template.to_dict())
        
        return results
    
    @staticmethod
    def create_agent_from_template(
        template_id: str,
        name: str,
        user_id: str,
        customizations: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create agent configuration from a template.
        
        Args:
            template_id: Template ID
            name: Agent name
            user_id: User ID
            customizations: Optional customizations to apply
            
        Returns:
            Agent configuration dictionary
        """
        template = AGENT_TEMPLATES.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        customizations = customizations or {}
        
        # Build agent configuration
        agent_config = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": name,
            "description": customizations.get("description", template.description),
            "agent_type": "template_based",
            "template_id": template_id,
            "llm_provider": customizations.get("llm_provider", template.recommended_provider),
            "llm_model": customizations.get("llm_model", template.recommended_model),
            "configuration": {
                "system_prompt": customizations.get("system_prompt", template.system_prompt),
                "temperature": customizations.get("temperature", template.temperature),
                "max_tokens": customizations.get("max_tokens", template.max_tokens),
                "enable_memory": customizations.get("enable_memory", template.enable_memory),
                "enable_streaming": customizations.get("enable_streaming", template.enable_streaming),
            },
            "tools": [
                {
                    "tool_id": tool.tool_id,
                    "configuration": {**tool.default_config, **customizations.get("tool_configs", {}).get(tool.tool_id, {})}
                }
                for tool in template.tools
            ],
            "requires_knowledgebase": template.requires_knowledgebase,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        return agent_config
    
    @staticmethod
    def get_categories() -> List[Dict[str, str]]:
        """Get all available categories."""
        return [
            {"id": c.value, "name": c.value.replace("_", " ").title()}
            for c in AgentCategory
        ]
    
    @staticmethod
    def get_complexity_levels() -> List[Dict[str, str]]:
        """Get all complexity levels."""
        descriptions = {
            AgentComplexity.SIMPLE: "Basic agent with minimal configuration",
            AgentComplexity.MODERATE: "Agent with multiple tools and structured prompts",
            AgentComplexity.ADVANCED: "Complex agent with RAG and advanced workflows",
        }
        return [
            {"id": c.value, "name": c.value.title(), "description": descriptions[c]}
            for c in AgentComplexity
        ]
