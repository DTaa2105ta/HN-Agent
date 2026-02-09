import os
import sys
import time

from dotenv import load_dotenv

try:
	from google import genai
except ImportError as exc:
	raise SystemExit(
		"Missing dependency: google-genai. Install with 'pip install google-genai'."
	) from exc


def require_env(name: str) -> str:
	value = os.getenv(name)
	if not value:
		raise SystemExit(f"Missing required environment variable: {name}")
	return value


def smoke_test(client: "genai.Client", model_id: str) -> None:
	prompt = "Write a single sentence explaining what an API key is."
	start = time.perf_counter()
	response = client.models.generate_content(model=model_id, contents=prompt)
	elapsed_ms = (time.perf_counter() - start) * 1000

	text = getattr(response, "text", "") or ""
	if not text.strip():
		raise RuntimeError("Empty response from model")

	print("Smoke test OK")
	print(f"Latency: {elapsed_ms:.0f} ms")
	print(f"Sample output: {text.strip()[:200]}")


def accuracy_test(client: "genai.Client", model_id: str) -> None:
	prompt = "Return only the sum of 127 and 391."
	response = client.models.generate_content(model=model_id, contents=prompt)
	text = (getattr(response, "text", "") or "").strip()

	if text != "518":
		raise RuntimeError(f"Unexpected answer: {text!r}")

	print("Accuracy test OK")


def main() -> None:
	load_dotenv()

	api_key = require_env("GEMINI_API_KEY")
	model_id = os.getenv("MODEL_ID", "gemini-2.5-flash")
	# Accept env formats like "gemini/gemini-2.5-flash" by stripping the prefix.
	if "/" in model_id:
		model_id = model_id.split("/")[-1]

	client = genai.Client(api_key=api_key)
	print(f"Using model: {model_id}")

	smoke_test(client, model_id)
	accuracy_test(client, model_id)


if __name__ == "__main__":
	try:
		main()
	except Exception as exc:
		print(f"Test failed: {exc}")
		sys.exit(1)
