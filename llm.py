import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def find_exclusions(user_message: str, cancellations: list) -> list:
    """
    Accepts a user message and a list of cancellations.
    Returns a list of guest names that should NOT be cancelled.
    """
    names = [c["name"] for c in cancellations]
    names_str = "\n".join([f"{i+1}. {name}" for i, name in enumerate(names)])

    logger.info(f"Sending exclusion request to LLM. Guests: {names}")

    system_prompt = """You are an assistant that analyzes user messages.
The user may refer to a guest by name (in any language), by number in the list, or by description ("last", "first", "4th").
Your task is to determine which guests should NOT be cancelled.
Reply ONLY with a valid JSON array of names. No text outside JSON.
Example: ["Johann Klußmann"]
If no one should be excluded — return an empty array: []"""

    user_prompt = f"""List of guests pending insurance cancellation:
{names_str}

User message: "{user_message}"

Who should NOT be cancelled? Return a JSON array of names."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        result = response.choices[0].message.content.strip()
        logger.debug(f"LLM raw response: {result}")

        exclusions = json.loads(result)
        logger.info(f"Exclusions identified: {exclusions}")
        return exclusions

    except json.JSONDecodeError:
        logger.warning(f"LLM returned invalid JSON: {result}")
        return []
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        return []