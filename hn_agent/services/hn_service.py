"""Hacker News API service with concurrent fetching."""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from hn_agent.utils.logger import logger


class HNService:
    """Service for fetching Hacker News data."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, max_retries: int = 2, timeout: int = 5) -> None:
        """Initialize HN Service."""
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HNAgent/1.0"})

    def get_top_stories(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch top stories from HN concurrently."""
        logger.info(f"Fetching top {count} stories")
        try:
            story_ids = self._fetch_with_retry(f"{self.BASE_URL}/topstories.json")
            if not story_ids:
                return []

            stories = self._fetch_items_concurrent(story_ids[:count])
            logger.info(f"Fetched {len(stories)} stories")
            return stories
        except Exception as e:
            logger.error(f"Error fetching top stories: {e}")
            return []

    def get_comments(self, story_id: int, max_comments: int = 5) -> List[Dict[str, Any]]:
        """Fetch comments for a story concurrently."""
        logger.info(f"Fetching comments for story {story_id}")
        try:
            story = self._fetch_with_retry(f"{self.BASE_URL}/item/{story_id}.json")
            if not story or "kids" not in story:
                return []

            comment_ids = story["kids"][:max_comments]
            comments = self._fetch_items_concurrent(
                comment_ids, item_type="comment"
            )
            logger.info(f"Fetched {len(comments)} comments")
            return comments
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            return []

    def _fetch_items_concurrent(
        self, item_ids: List[int], item_type: str = "story"
    ) -> List[Dict[str, Any]]:
        """Fetch multiple items in parallel."""
        results: List[Optional[Dict[str, Any]]] = [None] * len(item_ids)

        with ThreadPoolExecutor(max_workers=min(len(item_ids), 10)) as pool:
            future_to_idx = {
                pool.submit(self._fetch_item, iid, item_type): idx
                for idx, iid in enumerate(item_ids)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception:
                    pass

        return [r for r in results if r is not None]

    def _fetch_item(
        self, item_id: int, item_type: str = "story"
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single item (story or comment)."""
        data = self._fetch_with_retry(f"{self.BASE_URL}/item/{item_id}.json")
        if not data:
            return None

        if item_type == "comment":
            if data.get("type") != "comment":
                return None
            return {
                "id": data.get("id"),
                "text": data.get("text", ""),
                "by": data.get("by"),
                "time": data.get("time"),
                "score": data.get("score", 0),
            }

        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "url": data.get("url"),
            "score": data.get("score", 0),
            "by": data.get("by"),
            "time": data.get("time"),
            "descendants": data.get("descendants", 0),
            "kids": data.get("kids", []),
        }

    def _fetch_with_retry(self, url: str) -> Optional[Any]:
        """Fetch with retry logic."""
        import time

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    return None
                logger.warning(f"HTTP error {attempt + 1}/{self.max_retries}")
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout {attempt + 1}/{self.max_retries}")
            except Exception as e:
                logger.warning(f"Error {attempt + 1}/{self.max_retries}: {e}")

            if attempt < self.max_retries - 1:
                time.sleep(1)

        logger.error(f"Failed after {self.max_retries} attempts: {url}")
        return None
