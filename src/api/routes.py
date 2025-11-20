# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.
# See LICENSE file in the project root for full license information.
import json
import logging
import os
from typing import Dict

import fastapi
from fastapi import Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from azure.ai.inference.prompts import PromptTemplate
from azure.ai.inference.aio import ChatCompletionsClient

from .util import get_logger, ChatRequest
from .search_index_manager import SearchIndexManager
from azure.core.exceptions import HttpResponseError


from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import secrets

security = HTTPBasic()


username = os.getenv("WEB_APP_USERNAME")
password = os.getenv("WEB_APP_PASSWORD")
basic_auth = username and password

def authenticate(credentials: Optional[HTTPBasicCredentials] = Depends(security)) -> None:

    if not basic_auth:
        logger.info("Skipping authentication: WEB_APP_USERNAME or WEB_APP_PASSWORD not set.")
        return
    
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return

auth_dependency = Depends(authenticate) if basic_auth else None

logger = get_logger(
    name="azureaiapp_routes",
    log_level=logging.INFO,
    log_file_name=os.getenv("APP_LOG_FILE"),
    log_to_console=True
)

router = fastapi.APIRouter()
templates = Jinja2Templates(directory="api/templates")


# Accessors to get app state
def get_model_provider(request: Request):
    return request.app.state.model_provider


def get_chat_model(request: Request) -> str:
    return request.app.state.chat_model


def get_search_index_namager(request: Request) -> SearchIndexManager:
    return request.app.state.search_index_manager

def serialize_sse_event(data: Dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.get("/", response_class=HTMLResponse)
async def index_name(request: Request, _ = auth_dependency):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
        }
    )

@router.post("/chat")
async def chat_stream_handler(
    chat_request: ChatRequest,
    model_provider = Depends(get_model_provider),
    model_deployment_name: str = Depends(get_chat_model),
    search_index_manager: SearchIndexManager = Depends(get_search_index_namager),
    _ = auth_dependency
) -> fastapi.responses.StreamingResponse:

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream"
    }
    if model_provider is None:
        raise Exception("Model provider not initialized")

    async def response_stream():
        messages = [{"role": message.role, "content": message.content} for message in chat_request.messages]

        # Build system prompt
        system_prompt = "You are a helpful assistant"

        # Use RAG model, only if we were provided index and we have found a context there.
        if search_index_manager is not None:
            context = await search_index_manager.search(chat_request)
            if context:
                system_prompt = (
                    'You are a helpful assistant that answers some questions '
                    'with the help of some context data.\n\nHere is '
                    f'the context data:\n\n{context}'
                )
                logger.info("Using RAG context for response")
            else:
                logger.info("Unable to find the relevant information in the index for the request.")

        # Prepend system message
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        try:
            accumulated_message = ""

            # Use model provider's complete method
            async for event in model_provider.complete(
                model=model_deployment_name,
                messages=full_messages,
                stream=True
            ):
                if "error" in event:
                    yield serialize_sse_event(event)
                    return

                content = event.get("content", "")
                if content:
                    accumulated_message += content
                    yield serialize_sse_event({
                        "content": content,
                        "type": "message",
                    })

            yield serialize_sse_event({
                "content": accumulated_message,
                "type": "completed_message",
            })                        
        except BaseException as e:
            error_processed = False
            response = "There is an error!"
            try:
                if '(content_filter)' in e.args[0]:
                    rai_dict = e.response.json()['error']['innererror']['content_filter_result']
                    errors = []
                    for k, v in rai_dict.items():
                        if v['filtered']:
                            if 'severity' in v:
                                errors.append(f"{k}, severity: {v['severity']}")
                            else:
                                errors.append(k)
                    error_text = f"We have found the next safety issues in the response: {', '.join(errors)}"
                    logger.error(error_text)
                    response = error_text
                    error_processed = True
            except BaseException:
                pass
            if not error_processed:
                error_text = str(e)
                logger.error(error_text)
                response = error_text
            yield serialize_sse_event({
                            "content": response,
                            "type": "completed_message",
                        })
        yield serialize_sse_event({
            "type": "stream_end"
            })

    return StreamingResponse(response_stream(), headers=headers)
