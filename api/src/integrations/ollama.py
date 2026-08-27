from ollama import Client, AsyncClient

from src.config.config import Settings

class OllamaClient:
    def __init__(self, host: str):
        self.client = AsyncClient(host=host)

    async def list_models(self):
        return await self.client.list()

    async def running_models(self):
        return await self.client.ps()

    async def load_model(
        self,
        model: str,
        keep_alive: str | int = -1,
    ):
        return await self.client.generate(
            model=model,
            prompt="",
            keep_alive=keep_alive,
        )

    async def unload_model(self, model: str):
        return await self.client.generate(
            model=model,
            prompt="",
            keep_alive=0,
        )

class OllamaEmbeddingService:
    """Adaptador de nuestra aplicación hacia el servidor Ollama."""

    def __init__(self, settings: Settings) -> None:
        self._client = Client(
            host=settings.ollama_base_url,
            timeout=settings.ollama_timeout_seconds,
        )
        self._model = settings.ollama_embedding_model

    def embed(self, text: str) -> list[float]:
        response = self._client.embed(
            model=self._model,
            input=text,
        )
        return response["embeddings"][0]