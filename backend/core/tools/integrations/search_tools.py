"""Search tool integrations.

This module provides integrations for search services including:
- Tavily
- Serper
- Exa
- Wikipedia
- Arxiv
- Google Search
- Bing Search
- DuckDuckGo
"""

import logging

from backend.core.tools.registry import ToolRegistry
from backend.core.tools.base import ParamConfig, OutputConfig, RequestConfig
from backend.core.tools.response_transformer import ResponseTransformer

logger = logging.getLogger(__name__)


# Tavily Search
@ToolRegistry.register(
    tool_id="tavily_search",
    name="Tavily Search",
    description="AI-powered web search with Tavily",
    category="search",
    params={
        "query": ParamConfig(type="string", description="Search query", required=True),
        "search_depth": ParamConfig(
            type="string",
            description="Search depth",
            enum=["basic", "advanced"],
            default="basic"
        ),
        "max_results": ParamConfig(type="number", description="Maximum results", default=5)
    },
    outputs={
        "results": OutputConfig(type="array", description="Search results"),
        "answer": OutputConfig(type="string", description="AI-generated answer")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.tavily.com/search",
        headers={"Content-Type": "application/json"},
        body_template={
            "query": "{{query}}",
            "search_depth": "{{search_depth}}",
            "max_results": "{{max_results}}"
        }
    ),
    api_key_env="TAVILY_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"results": "results", "answer": "answer"}
    ),
    icon="search",
    bg_color="#6366F1",
    docs_link="https://docs.tavily.com/"
)
class TavilySearchTool:
    pass


# Serper Google Search
@ToolRegistry.register(
    tool_id="serper_search",
    name="Serper Google Search",
    description="Google Search via Serper API",
    category="search",
    params={
        "q": ParamConfig(type="string", description="Search query", required=True),
        "num": ParamConfig(type="number", description="Number of results", default=10),
        "type": ParamConfig(
            type="string",
            description="Search type",
            enum=["search", "images", "news", "places"],
            default="search"
        )
    },
    outputs={
        "organic": OutputConfig(type="array", description="Organic search results"),
        "answer_box": OutputConfig(type="object", description="Answer box")
    },
    request=RequestConfig(
        method="POST",
        url="https://google.serper.dev/{{type}}",
        headers={"Content-Type": "application/json"},
        body_template={"q": "{{q}}", "num": "{{num}}"}
    ),
    api_key_env="SERPER_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"organic": "organic", "answer_box": "answerBox"}
    ),
    icon="search",
    bg_color="#4285F4",
    docs_link="https://serper.dev/docs"
)
class SerperSearchTool:
    pass


# Exa Search
@ToolRegistry.register(
    tool_id="exa_search",
    name="Exa Search",
    description="Neural search with Exa",
    category="search",
    params={
        "query": ParamConfig(type="string", description="Search query", required=True),
        "num_results": ParamConfig(type="number", description="Number of results", default=10),
        "type": ParamConfig(
            type="string",
            description="Search type",
            enum=["neural", "keyword"],
            default="neural"
        )
    },
    outputs={
        "results": OutputConfig(type="array", description="Search results")
    },
    request=RequestConfig(
        method="POST",
        url="https://api.exa.ai/search",
        headers={"Content-Type": "application/json"},
        body_template={
            "query": "{{query}}",
            "num_results": "{{num_results}}",
            "type": "{{type}}"
        }
    ),
    api_key_env="EXA_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"results": "results"}
    ),
    icon="search",
    bg_color="#000000",
    docs_link="https://docs.exa.ai/"
)
class ExaSearchTool:
    pass


# Wikipedia Search
@ToolRegistry.register(
    tool_id="wikipedia_search",
    name="Wikipedia Search",
    description="Search Wikipedia articles",
    category="search",
    params={
        "query": ParamConfig(type="string", description="Search query", required=True),
        "limit": ParamConfig(type="number", description="Number of results", default=5)
    },
    outputs={
        "results": OutputConfig(type="array", description="Search results")
    },
    request=RequestConfig(
        method="GET",
        url="https://en.wikipedia.org/w/api.php",
        query_params={
            "action": "query",
            "list": "search",
            "srsearch": "{{query}}",
            "srlimit": "{{limit}}",
            "format": "json"
        }
    ),
    transform_response=ResponseTransformer.create_transformer(
        array_path="query.search"
    ),
    icon="book-open",
    bg_color="#000000",
    docs_link="https://www.mediawiki.org/wiki/API:Search"
)
class WikipediaSearchTool:
    pass


# Arxiv Search
@ToolRegistry.register(
    tool_id="arxiv_search",
    name="Arxiv Search",
    description="Search academic papers on Arxiv",
    category="search",
    params={
        "query": ParamConfig(type="string", description="Search query", required=True),
        "max_results": ParamConfig(type="number", description="Maximum results", default=10)
    },
    outputs={
        "results": OutputConfig(type="array", description="Paper results")
    },
    request=RequestConfig(
        method="GET",
        url="http://export.arxiv.org/api/query",
        query_params={
            "search_query": "all:{{query}}",
            "max_results": "{{max_results}}"
        }
    ),
    transform_response=lambda x: {"results": x.get("entry", [])},
    icon="file-text",
    bg_color="#B31B1B",
    docs_link="https://info.arxiv.org/help/api/index.html"
)
class ArxivSearchTool:
    pass


# Google Custom Search
@ToolRegistry.register(
    tool_id="google_custom_search",
    name="Google Custom Search",
    description="Search using Google Custom Search API",
    category="search",
    params={
        "q": ParamConfig(type="string", description="Search query", required=True),
        "cx": ParamConfig(type="string", description="Custom search engine ID", required=True),
        "num": ParamConfig(type="number", description="Number of results", default=10)
    },
    outputs={
        "items": OutputConfig(type="array", description="Search results")
    },
    request=RequestConfig(
        method="GET",
        url="https://www.googleapis.com/customsearch/v1",
        query_params={
            "key": "{{api_key}}",
            "cx": "{{cx}}",
            "q": "{{q}}",
            "num": "{{num}}"
        }
    ),
    api_key_env="GOOGLE_CUSTOM_SEARCH_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"items": "items"}
    ),
    icon="search",
    bg_color="#4285F4",
    docs_link="https://developers.google.com/custom-search/v1/overview"
)
class GoogleCustomSearchTool:
    pass


# Bing Web Search
@ToolRegistry.register(
    tool_id="bing_search",
    name="Bing Web Search",
    description="Search the web using Bing Search API",
    category="search",
    params={
        "q": ParamConfig(type="string", description="Search query", required=True),
        "count": ParamConfig(type="number", description="Number of results", default=10),
        "mkt": ParamConfig(type="string", description="Market code", default="en-US")
    },
    outputs={
        "webPages": OutputConfig(type="object", description="Web page results")
    },
    request=RequestConfig(
        method="GET",
        url="https://api.bing.microsoft.com/v7.0/search",
        headers={"Ocp-Apim-Subscription-Key": "{{api_key}}"},
        query_params={
            "q": "{{q}}",
            "count": "{{count}}",
            "mkt": "{{mkt}}"
        }
    ),
    api_key_env="BING_SEARCH_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"webPages": "webPages"}
    ),
    icon="search",
    bg_color="#008373",
    docs_link="https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/overview"
)
class BingSearchTool:
    pass


# DuckDuckGo Search
@ToolRegistry.register(
    tool_id="duckduckgo_search",
    name="DuckDuckGo Search",
    description="Search using DuckDuckGo Instant Answer API",
    category="search",
    params={
        "q": ParamConfig(type="string", description="Search query", required=True),
        "format": ParamConfig(type="string", description="Response format", default="json")
    },
    outputs={
        "results": OutputConfig(type="array", description="Search results"),
        "abstract": OutputConfig(type="string", description="Abstract text")
    },
    request=RequestConfig(
        method="GET",
        url="https://api.duckduckgo.com/",
        query_params={
            "q": "{{q}}",
            "format": "{{format}}"
        }
    ),
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"results": "RelatedTopics", "abstract": "AbstractText"}
    ),
    icon="search",
    bg_color="#DE5833",
    docs_link="https://duckduckgo.com/api"
)
class DuckDuckGoSearchTool:
    pass


# YouTube Search
@ToolRegistry.register(
    tool_id="youtube_search",
    name="YouTube Search",
    description="Search YouTube videos using YouTube Data API",
    category="search",
    params={
        "q": ParamConfig(type="string", description="Search query", required=True),
        "maxResults": ParamConfig(type="number", description="Maximum results", default=10),
        "type": ParamConfig(
            type="string",
            description="Resource type",
            enum=["video", "channel", "playlist"],
            default="video"
        ),
        "order": ParamConfig(
            type="string",
            description="Sort order",
            enum=["relevance", "date", "rating", "viewCount", "title"],
            default="relevance"
        )
    },
    outputs={
        "items": OutputConfig(type="array", description="Video search results")
    },
    request=RequestConfig(
        method="GET",
        url="https://www.googleapis.com/youtube/v3/search",
        query_params={
            "key": "{{api_key}}",
            "q": "{{q}}",
            "maxResults": "{{maxResults}}",
            "type": "{{type}}",
            "order": "{{order}}",
            "part": "snippet"
        }
    ),
    api_key_env="YOUTUBE_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"items": "items"}
    ),
    icon="video",
    bg_color="#FF0000",
    docs_link="https://developers.google.com/youtube/v3/docs/search/list"
)
class YouTubeSearchTool:
    pass


logger.info("Registered 9 search tools")
