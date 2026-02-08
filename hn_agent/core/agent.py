"""HackerNews Agent using smolagents CodeAgent."""
import logging
from typing import Optional

from smolagents import CodeAgent, InferenceClientModel, LiteLLMModel, OpenAIServerModel
from smolagents.models import ApiModel
from smolagents.monitoring import LogLevel

from hn_agent.core.prompts import AGENT_DESCRIPTION, AGENT_INSTRUCTIONS, AGENT_NAME
from hn_agent.tools.tools import ExtractCommentInsightsTool, FetchTopStoriesToolTool
from hn_agent.utils.logger import logger


def _build_model(
    provider: str,
    model_id: str,
    hf_token: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
) -> ApiModel:
    """Build the right model instance based on the provider setting."""
    if provider == "openai":
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when MODEL_PROVIDER=openai")
        logger.info(f"Using OpenAI provider with model: {model_id}")
        return OpenAIServerModel(model_id=model_id, api_key=openai_api_key)

    if provider == "gemini":
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when MODEL_PROVIDER=gemini")
        logger.info(f"Using Gemini provider with model: {model_id}")
        return LiteLLMModel(model_id=model_id, api_key=gemini_api_key)

    if provider == "hf_inference":
        logger.info(f"Using HF Inference provider with model: {model_id}")
        return InferenceClientModel(model_id=model_id, token=hf_token)

    raise ValueError(
        f"Unknown MODEL_PROVIDER '{provider}'. Use 'openai', 'gemini', or 'hf_inference'."
    )


def create_hn_agent(
    provider: str = "gemini",
    model_id: str = "gemini/gemini-2.5-flash",
    hf_token: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    max_steps: int = 6,
) -> CodeAgent:
    """Create a configured HackerNews CodeAgent."""
    logger.info(f"Creating HN agent (provider={provider}, model={model_id})")

    tools = [
        FetchTopStoriesToolTool(),
        ExtractCommentInsightsTool(),
    ]

    logger.info(f"Loaded {len(tools)} tools: {[t.name for t in tools]}")

    model = _build_model(
        provider=provider,
        model_id=model_id,
        hf_token=hf_token,
        openai_api_key=openai_api_key,
        gemini_api_key=gemini_api_key,
    )

    # Enable smolagents internal logger for terminal visibility
    smolagents_logger = logging.getLogger("smolagents")
    if not smolagents_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        smolagents_logger.addHandler(handler)
    smolagents_logger.setLevel(logging.DEBUG)

    agent = CodeAgent(
        tools=tools,
        model=model,
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        instructions=AGENT_INSTRUCTIONS,
        max_steps=max_steps,
        verbosity_level=LogLevel.DEBUG,
    )

    logger.info("HN agent created successfully")
    return agent
