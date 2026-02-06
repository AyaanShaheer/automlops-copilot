from typing import Optional
from google import genai
from groq import Groq
from loguru import logger
from src.config import settings


class LLMClient:
    """Unified client for Gemini and Groq LLMs (NEW Gemini SDK)"""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER

        if self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set in environment")

            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model = settings.GEMINI_MODEL
            logger.info(f"Initialized Gemini with model: {self.model}")

        elif self.provider == "groq":
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not set in environment")

            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = settings.GROQ_MODEL
            logger.info(f"Initialized Groq with model: {self.model}")

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate(self, prompt: str, max_tokens: int = 4096, temperature: float = 0.1) -> str:
        """Generate text from prompt"""
        try:
            if self.provider == "gemini":
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                return response.text

            elif self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        """Generate with system and user prompts"""
        try:
            if self.provider == "gemini":
                combined = f"{system_prompt}\n\n{user_prompt}"
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=combined,
                )
                return response.text

            elif self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM generation with system prompt failed: {e}")
            raise
