# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.
# See LICENSE file in the project root for full license information.
"""
Model provider abstraction for supporting multiple LLM backends.

Supports:
- Azure OpenAI
- Self-hosted models (Ollama, LocalAI, LM Studio, vLLM)
- Any OpenAI-compatible API
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List
import aiohttp

logger = logging.getLogger("azureaiapp")


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    @abstractmethod
    async def complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = True
    ) -> AsyncIterator[Dict]:
        """Generate completion from the model."""
        pass

    @abstractmethod
    async def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available models."""
        pass

    @abstractmethod
    async def close(self):
        """Cleanup resources."""
        pass


class AzureOpenAIProvider(ModelProvider):
    """Provider for Azure OpenAI Service."""

    def __init__(self, chat_client, default_model: str, available_models: List[str] = None):
        self.chat_client = chat_client
        self.default_model = default_model
        self.available_models = available_models or [default_model]

    async def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available Azure OpenAI models."""
        return [
            {
                "id": model,
                "name": model,
                "provider": "azure"
            }
            for model in self.available_models
        ]

    async def complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = True
    ) -> AsyncIterator[Dict]:
        """Generate completion using Azure OpenAI."""
        model_name = model or self.default_model

        chat_coroutine = await self.chat_client.complete(
            model=model_name,
            messages=messages,
            stream=stream
        )

        async for event in chat_coroutine:
            if event.choices:
                first_choice = event.choices[0]
                if first_choice.delta.content:
                    yield {
                        "content": first_choice.delta.content,
                        "type": "message",
                        "model": model_name
                    }

    async def close(self):
        """Close Azure client."""
        await self.chat_client.close()


class OpenAICompatibleProvider(ModelProvider):
    """Provider for OpenAI-compatible APIs (Ollama, LocalAI, LM Studio, etc.)."""

    def __init__(
        self,
        base_url: str,
        default_model: str,
        api_key: str = "not-needed"
    ):
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.api_key = api_key
        self.session = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available models from the API."""
        await self._ensure_session()

        try:
            # Try to get models from /v1/models endpoint (OpenAI-compatible)
            endpoint = f"{self.base_url}/v1/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.get(endpoint, headers=headers, timeout=5) as response:
                if response.ok:
                    data = await response.json()
                    models = []

                    # Handle different response formats
                    if isinstance(data, dict) and 'data' in data:
                        # OpenAI format
                        for model in data['data']:
                            model_id = model.get('id', model.get('name', 'unknown'))
                            models.append({
                                "id": model_id,
                                "name": model_id,
                                "provider": "local"
                            })
                    elif isinstance(data, dict) and 'models' in data:
                        # Ollama format
                        for model in data['models']:
                            model_name = model.get('name', model.get('model', 'unknown'))
                            models.append({
                                "id": model_name,
                                "name": model_name,
                                "provider": "ollama"
                            })
                    elif isinstance(data, list):
                        # Simple list format
                        for model in data:
                            if isinstance(model, str):
                                models.append({
                                    "id": model,
                                    "name": model,
                                    "provider": "local"
                                })
                            elif isinstance(model, dict):
                                model_id = model.get('id', model.get('name', 'unknown'))
                                models.append({
                                    "id": model_id,
                                    "name": model_id,
                                    "provider": "local"
                                })

                    if models:
                        return models

        except Exception as e:
            logger.warning(f"Could not fetch models from API: {e}")

        # Fallback: return default model
        return [{
            "id": self.default_model,
            "name": self.default_model,
            "provider": "local"
        }]

    async def complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = True
    ) -> AsyncIterator[Dict]:
        """Generate completion using OpenAI-compatible API."""
        await self._ensure_session()

        model_name = model or self.default_model
        endpoint = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": stream
        }

        try:
            async with self.session.post(
                endpoint,
                json=payload,
                headers=headers
            ) as response:
                if not response.ok:
                    error_text = await response.text()
                    logger.error(
                        f"Model API error: {response.status} - {error_text}"
                    )
                    yield {
                        "error": {
                            "message": f"Model API error: {response.status}"
                        }
                    }
                    return

                if stream:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            if line == 'data: [DONE]':
                                break

                            try:
                                import json
                                data = json.loads(line[6:])

                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')

                                    if content:
                                        yield {
                                            "content": content,
                                            "type": "message",
                                            "model": model_name
                                        }
                            except json.JSONDecodeError:
                                continue
                else:
                    data = await response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        yield {
                            "content": content,
                            "type": "completed_message",
                            "model": model_name
                        }

        except aiohttp.ClientError as e:
            logger.error(f"Connection error to model API: {e}")
            yield {
                "error": {
                    "message": f"Could not connect to model API: {str(e)}"
                }
            }

    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None


def create_model_provider(
    provider_type: str,
    **kwargs
) -> ModelProvider:
    """
    Factory function to create the appropriate model provider.

    Args:
        provider_type: "azure" or "openai-compatible"
        **kwargs: Provider-specific arguments

    Returns:
        ModelProvider instance
    """
    if provider_type == "azure":
        return AzureOpenAIProvider(
            chat_client=kwargs['chat_client'],
            default_model=kwargs['default_model']
        )
    elif provider_type == "openai-compatible":
        return OpenAICompatibleProvider(
            base_url=kwargs['base_url'],
            default_model=kwargs['default_model'],
            api_key=kwargs.get('api_key', 'not-needed')
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
