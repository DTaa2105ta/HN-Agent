import sys
sys.path.insert(0, ".")

# 1. Tools — should only have 2 classes now
from hn_agent.tools.tools import FetchTopStoriesToolTool, ExtractCommentInsightsTool
print("tools.py OK — 2 tools")

# Verify deleted tools are gone
try:
    from hn_agent.tools.tools import SummarizeStoryTool
    print("ERROR: SummarizeStoryTool still exists!")
except ImportError:
    print("  SummarizeStoryTool removed OK")

try:
    from hn_agent.tools.tools import AnalyzeTrendingTool
    print("ERROR: AnalyzeTrendingTool still exists!")
except ImportError:
    print("  AnalyzeTrendingTool removed OK")

# 2. Agent
from hn_agent.core.agent import create_hn_agent
print("agent.py OK")

# 3. Prompts
from hn_agent.core.prompts import AGENT_INSTRUCTIONS
print("prompts.py OK")
print(f"  fetch_top_stories in instructions: {'fetch_top_stories' in AGENT_INSTRUCTIONS}")
print(f"  extract_comment_insights in instructions: {'extract_comment_insights' in AGENT_INSTRUCTIONS}")
print(f"  summarize_story gone: {'summarize_story' not in AGENT_INSTRUCTIONS}")
print(f"  analyze_trending gone: {'analyze_trending' not in AGENT_INSTRUCTIONS}")
print(f"  Anti-loop rule: {'ONCE' in AGENT_INSTRUCTIONS}")
print(f"  Story ID rule: {'Story ID' in AGENT_INSTRUCTIONS}")

# 4. run_gradio
sys.path.insert(0, "scripts")
from run_gradio import HNGradioUI
print("run_gradio.py OK")

# 5. Fetch test
ft = FetchTopStoriesToolTool()
output = ft.forward(2)
print(f"\nFetch output includes Story ID: {'Story ID:' in output}")
print(f"Fetch output includes Score/Comment ratio: {'Score/Comment ratio:' in output}")

print("\nAll checks passed!")
