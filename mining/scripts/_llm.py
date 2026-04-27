"""Shared LLM helper for mining scripts.

Uses the LiteLLM proxy (OpenAI-compatible) with env vars:
- OPENAI_API_BASE  (proxy base URL)
- OPENAI_API_KEY   (proxy key)
- LLM_MODEL        (optional default, e.g. "anthropic.claude-4.5-sonnet")

Model naming convention in this repo is provider-prefixed:
- Sonnet:  "anthropic.claude-4.5-sonnet"
- Haiku:   "anthropic.claude-4.5-haiku"  (proxy-confirmed name)
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import AuthenticationError, OpenAI, RateLimitError

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(REPO_ROOT / ".env")

DEFAULT_MODEL = os.environ.get("LLM_MODEL", "anthropic.claude-4.5-sonnet")
HAIKU_MODEL = "anthropic.claude-4.5-haiku"
SONNET_MODEL = "anthropic.claude-4.5-sonnet"
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "openai.text-embedding-3-small")

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        base = os.environ.get("OPENAI_API_BASE")
        key = os.environ.get("OPENAI_API_KEY")
        if not base or not key:
            raise RuntimeError("OPENAI_API_BASE and OPENAI_API_KEY must be set")
        _client = OpenAI(base_url=base, api_key=key, timeout=90.0, max_retries=0)
    return _client


_FENCE = re.compile(r"^```(?:json)?\s*\n?|\n?```\s*$", re.MULTILINE)


def _extract_json(text: str):
    s = _FENCE.sub("", text).strip()
    # Try the whole thing first
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # Fallback: first JSON array or object
    for open_c, close_c in (("[", "]"), ("{", "}")):
        if open_c in s and close_c in s:
            start = s.index(open_c)
            end = s.rindex(close_c) + 1
            try:
                return json.loads(s[start:end])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not parse JSON from response: {text[:200]!r}")


def chat_json(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 500,
    temperature: float = 0.0,
    max_retries: int = 5,
):
    """Send a chat prompt and return the parsed JSON response.

    Retries with exponential backoff on rate limit or transient errors.
    Returns either a dict or a list depending on what the model emits.
    """
    client = get_client()
    model = model or DEFAULT_MODEL
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = resp.choices[0].message.content or ""
            return _extract_json(text)
        except AuthenticationError:
            # Auth/permission errors don't get better with retries.
            raise
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait = min(5 * (2**attempt), 120) + random.uniform(0, 2)
            logger.warning(f"rate limited, retrying in {wait:.1f}s: {e}")
            time.sleep(wait)
        except ValueError:
            # JSON parse failure — retry once with higher max_tokens in case we got cut off
            if attempt == max_retries - 1:
                raise
            max_tokens = min(max_tokens * 2, 4000)
            logger.warning(f"JSON parse failure, retrying with max_tokens={max_tokens}")
        except Exception as e:
            # Treat proxy 401s as auth failures even if not surfaced as AuthenticationError.
            if "401" in str(e) or "team_model_access_denied" in str(e):
                raise
            if attempt == max_retries - 1:
                raise
            wait = min(2 ** (attempt + 1), 32)
            logger.warning(f"LLM error attempt {attempt + 1}/{max_retries}: {e}; retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def embed_texts(
    texts: list[str],
    batch_size: int = 100,
    max_retries: int = 7,
) -> list[list[float]]:
    """Embed multiple texts in batches. Returns list of vectors.

    Uses batching to stay within API limits and retries with exponential backoff.
    """
    client = get_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        for attempt in range(max_retries):
            try:
                response = client.embeddings.create(input=batch, model=EMBEDDING_MODEL)
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                break
            except (RateLimitError, AuthenticationError) as e:
                if "401" in str(e) or "team_model_access_denied" in str(e):
                    raise
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"LLM error attempt {attempt + 1}/{max_retries}: {e}; retrying in {delay:.0f}s")
                    time.sleep(delay)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"LLM error attempt {attempt + 1}/{max_retries}: {e}; retrying in {delay:.0f}s")
                    time.sleep(delay)
                else:
                    raise

    return all_embeddings
