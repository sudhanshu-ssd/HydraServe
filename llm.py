from groq import AsyncGroq
import os
from config import settings


class Groq_Demon:
    def __init__(self,model:str = 'openai/gpt-oss-120b'):
        self.client = AsyncGroq(api_key=settings.Groq_api_key.get_secret_value())
        self.model = model

    async def generate(self,user_prompt: str, 
                       system_prompt: str = "you are all around help assistant",
                       temperature: float = 0,
                 max_tokens: int = 1024,
                 top_p: float = 1):
        
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )
        return completion
    

