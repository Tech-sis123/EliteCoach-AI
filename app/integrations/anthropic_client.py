import anthropic
from app.core.config import settings
from app.core.logging import logger

class AnthropicClient:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def get_completion(self, system_prompt: str, messages: list):
        try:
            if settings.ANTHROPIC_API_KEY == "mock":
                return "This is a mock response from the AI Tutor."
                
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error("anthropic_error", error=str(e))
            if "credit balance" in str(e).lower() or "api_key" in str(e).lower():
                return "I'm currently having trouble connecting to my brain, but I've noted your message. Would you like me to escalate this to a human tutor?"
            raise

anthropic_client = AnthropicClient()
