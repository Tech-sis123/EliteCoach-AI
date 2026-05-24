from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import logger

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def get_embedding(self, text: str):
        try:
            response = await self.client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("openai_embedding_error", error=str(e))
            raise

openai_client = OpenAIClient()
