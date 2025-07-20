from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any
from dotenv import load_dotenv
from utilities.utils import load_text_file
from utilities.llm_utils import openai_guardrail, GuardRailResponse


class GuardRail:
    def __init__(self, sensitive_topics: List[str]):
        self.sensitive_topics = sensitive_topics

    def validate(self, text: str) -> Dict[str, Any]:
        prompt = self._create_prompt(text)
        guard_response = openai_guardrail(prompt)
        print(guard_response)
        if guard_response['is_sensitive']:
            try:
                if guard_response['is_sensitive']:
                    raise Exception(f"Sensitive content detected: {guard_response['explanation']}")
                return {"is_sensitive": False, "explanation": guard_response['explanation']}
            except ValidationError as e:
                print(f"Validation error: {str(e)}")
                raise Exception("Failed to validate the response")
        else:
            raise Exception("Failed to validate the response")

    def _create_prompt(self, text: str) -> List[Dict[str, str]]:
        prompt = [
            {"role": "system", "content": load_text_file('utilities/prompts/guardrail.txt').format(sensitive_topics=', '.join(self.sensitive_topics))},
            {"role": "user", "content": f"Please analyze the following text:\n\n{text}"}
        ]
        return prompt

# Usage example
guard = GuardRail(sensitive_topics=["politics", "religion", "violence"])

# Test passing response
try:
    result = guard.validate("San Francisco is known for its cool summers, fog, steep rolling hills, eclectic mix of architecture, and landmarks, including the Golden Gate Bridge, cable cars, the former Alcatraz Federal Penitentiary, Fisherman's Wharf, and its Chinatown district.")
    print("Passed validation:", result)
except Exception as e:
    print("Failed validation:", str(e))

# Test failing response
try:
    guard.validate("Donald Trump is one of the most controversial presidents in the history of the United States. He has been impeached twice, and is running for re-election in 2024.")
except Exception as e:
    print("Failed validation:", str(e))