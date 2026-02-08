"""Custom tools for HN Agent using smolagents Tool interface."""
from smolagents import Tool

from hn_agent.services.hn_service import HNService
from hn_agent.utils.logger import logger


class FetchTopStoriesToolTool(Tool):
    """Tool to fetch top stories from Hacker News."""

    name = "fetch_top_stories"
    description = (
        "Fetches the top N trending stories from Hacker News. "
        "Returns story ID, title, score, comment count, URL, and engagement metrics."
    )
    inputs = {
        "num_stories": {
            "type": "integer",
            "description": "Number of top stories to fetch (1-10). Default is 5.",
            "nullable": True,
        }
    }
    output_type = "string"

    def __init__(self) -> None:
        super().__init__()
        self.hn_service = HNService()

    def forward(self, num_stories: int = 5) -> str:
        num_stories = max(1, min(num_stories or 5, 10))
        logger.info(f"Tool: Fetching {num_stories} top stories")

        try:
            stories = self.hn_service.get_top_stories(count=num_stories)
            if not stories:
                return "No stories found on Hacker News right now."

            result = []
            for i, story in enumerate(stories, 1):
                score = story.get("score", 0)
                comments = story.get("descendants", 0)
                ratio = f"{score / max(comments, 1):.1f}"

                result.append(
                    f"#{i}\n"
                    f"Story ID: {story.get('id')}\n"
                    f"Title: {story.get('title', 'N/A')}\n"
                    f"Score: {score} | Comments: {comments} | Score/Comment ratio: {ratio}\n"
                    f"URL: {story.get('url', 'N/A')}\n"
                    f"Author: {story.get('by', 'Unknown')}\n"
                )

            return "\n".join(result)
        except Exception as e:
            logger.error(f"Error in fetch_top_stories: {e}")
            return f"Error fetching stories: {e}"


class ExtractCommentInsightsTool(Tool):
    """Tool to extract and summarize key insights from comments."""

    name = "extract_comment_insights"
    description = (
        "Extracts top comments and discussion themes from a Hacker News story. "
        "Requires the numeric Story ID (integer) from fetch_top_stories output."
    )
    inputs = {
        "story_id": {
            "type": "integer",
            "description": "Numeric Hacker News story ID (e.g. 42415051). Get this from the 'Story ID' field in fetch_top_stories output.",
        },
        "max_comments": {
            "type": "integer",
            "description": "Maximum number of top comments to analyze (default: 5)",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self) -> None:
        super().__init__()
        self.hn_service = HNService()

    def forward(self, story_id: int, max_comments: int = 5) -> str:
        # Validate story_id is a real HN item ID
        if not isinstance(story_id, int) or story_id < 1:
            return (
                f"Invalid story_id: {story_id}. "
                "Please pass the numeric Story ID from fetch_top_stories output "
                "(e.g. 42415051), not a URL or index number."
            )

        max_comments = max(1, min(max_comments or 5, 20))
        logger.info(f"Tool: Extracting insights from story {story_id}")

        try:
            comments = self.hn_service.get_comments(story_id, max_comments)
            if not comments:
                return f"No comments found for story {story_id}."

            insights = []
            for i, comment in enumerate(comments, 1):
                text = comment.get("text", "")
                text = text[:300] + "..." if len(text) > 300 else text
                author = comment.get("by", "anonymous")
                insights.append(f"Comment {i} (by {author}):\n{text}\n")

            result = f"Top {len(comments)} comments for story {story_id}:\n\n"
            result += "\n".join(insights)
            result += "\n\nKey Themes: " + self._extract_themes(comments)
            return result
        except Exception as e:
            logger.error(f"Error in extract_comment_insights: {e}")
            return f"Error extracting insights: {e}"

    @staticmethod
    def _extract_themes(comments: list) -> str:
        all_text = " ".join([c.get("text", "").lower() for c in comments])

        themes = []
        if any(w in all_text for w in ["bug", "issue", "problem", "error"]):
            themes.append("Technical Issues")
        if any(w in all_text for w in ["love", "great", "amazing", "awesome"]):
            themes.append("Positive Sentiment")
        if any(w in all_text for w in ["performance", "speed", "fast", "slow"]):
            themes.append("Performance")
        if any(w in all_text for w in ["security", "privacy", "vulnerability"]):
            themes.append("Security & Privacy")
        if any(w in all_text for w in ["ai", "llm", "gpt", "model", "machine learning"]):
            themes.append("AI & ML")

        return ", ".join(themes) if themes else "General Discussion"
