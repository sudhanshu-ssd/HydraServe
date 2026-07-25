from groq import AsyncGroq
from config import settings
from google import genai
from google.genai import types


class GroqProvider:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.Groq_api_key.get_secret_value())

    async def generate(self,user_prompt: str, 
                       system_prompt: str = "you are all around help assistant",
                       model:str = 'openai/gpt-oss-120b',
                       temperature: float = 0,
                 max_tokens: int = 1024,
                 top_p: float = 1):
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content,response.usage.total_tokens,response.usage.prompt_tokens,response.usage.completion_tokens




class GeminiProvider:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_key.get_secret_value())

    async def generate(self,user_prompt: str, 
                       system_prompt: str = "you are all around help assistant",
                       model:str = "gemini-3.1-flash-lite",
                       temperature: float = 0,
                       max_tokens: int = 1024,
                       top_k: float = 1):
        
        response = await self.client.aio.models.generate_content(model=model,
                                                        contents=user_prompt,
                                                       config=types.GenerateContentConfig(system_instruction=system_prompt,
                                                                                          temperature=temperature,
                                                                                          top_k=top_k,
                                                                                          max_output_tokens = max_tokens)
                                                       )
        
        return response.text,response.usage_metadata.total_token_count,response.usage_metadata.prompt_token_count,response.usage_metadata.candidates_token_count



Provider_dict = {'Groq':GroqProvider(),
                 "Gemini":GeminiProvider()}


Provider_Fallback = {"Groq": ("Gemini", "gemini-3.1-flash-lite"),
                     "Gemini":("Groq","openai/gpt-oss-120b")}   #we will create a table once we have more providers lol

