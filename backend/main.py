"""FastAPI backend for generating localized product content using OpenAI models."""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl, ValidationError

try:
    from openai import AsyncOpenAI
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise RuntimeError("openai package is required. Did you install backend/requirements.txt?") from exc


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is required.")


client = AsyncOpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="Catalog Builder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=150)
    keywords: List[str] = Field(default_factory=list)
    country: str = Field(..., min_length=2, max_length=120)
    language: str = Field(..., min_length=2, max_length=60)


class Source(BaseModel):
    name: str
    url: HttpUrl


class GenerateResponse(BaseModel):
    product_description: str
    bullet_points: List[str]
    marketing_blurb: str
    image_urls: List[HttpUrl]
    sources: List[Source]


SYSTEM_PROMPT = (
    "You are an e-commerce localization expert. Given a product name, optional keywords, "
    "target country, and target language, create localized marketing content. "
    "Output JSON with keys 'product_description' (markdown), 'bullet_points' (array of 3-5 "
    "concise localized selling points), 'marketing_blurb' (one short paragraph), and 'sources' "
    "(array of objects with 'name' and 'url' for reputable retailers that are likely to carry the product). "
    "All copy must be written in the requested language. Invent sources only if you cannot find real ones, "
    "but prefer well-known international or regional retailers that ship to the target country."
)

IMAGE_PROMPT_TEMPLATE = (
    "Generate a product photo style image for '{product_name}'. The image should align with the "
    "following marketing context: {bullet_points}. Style: clean studio lighting, realistic photography."
)


async def create_product_brief(payload: GenerateRequest) -> Dict[str, Any]:
    """Use the OpenAI Responses API to craft localized marketing copy."""
    response = await client.responses.create(
        model="gpt-4.1-mini",
        temperature=0.7,
        reasoning={"effort": "medium"},
        input=[
            {
                "role": "system",
                "content": [{"type": "text", "text": SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Product name: {name}\nKeywords: {keywords}\nCountry: {country}\nLanguage: {language}\n"
                        ).format(
                            name=payload.product_name,
                            keywords=", ".join(payload.keywords) or "(none)",
                            country=payload.country,
                            language=payload.language,
                        ),
                    }
                ],
            },
        ],
        response_format={"type": "json_schema", "json_schema": {
            "name": "product_content",
            "schema": {
                "type": "object",
                "properties": {
                    "product_description": {"type": "string"},
                    "bullet_points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 3,
                        "maxItems": 6,
                    },
                    "marketing_blurb": {"type": "string"},
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "url": {"type": "string", "format": "uri"},
                            },
                            "required": ["name", "url"],
                        },
                    },
                },
                "required": [
                    "product_description",
                    "bullet_points",
                    "marketing_blurb",
                    "sources",
                ],
                "additionalProperties": False,
            },
        }},
    )

    try:
        parsed = response.output[0].content[0].parsed  # type: ignore[attr-defined]
    except (AttributeError, IndexError) as exc:
        raise HTTPException(status_code=502, detail="Malformed response from language model") from exc

    return parsed


async def create_product_images(product_name: str, bullet_points: List[str]) -> List[str]:
    """Generate one or more product image URLs via the OpenAI Images API."""
    prompt = IMAGE_PROMPT_TEMPLATE.format(
        product_name=product_name,
        bullet_points="; ".join(bullet_points[:3]),
    )

    response = await client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return [data.url for data in response.data if getattr(data, "url", None)]


@app.post("/generate", response_model=GenerateResponse)
async def generate_content(payload: GenerateRequest) -> GenerateResponse:
    try:
        brief = await create_product_brief(payload)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        bullet_points = brief["bullet_points"]
        image_urls = await create_product_images(payload.product_name, bullet_points)
    except Exception as exc:  # pragma: no cover - image generation errors
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}") from exc

    try:
        response = GenerateResponse(
            product_description=brief["product_description"],
            bullet_points=bullet_points,
            marketing_blurb=brief["marketing_blurb"],
            image_urls=image_urls,
            sources=[Source(**source) for source in brief["sources"]],
        )
    except (ValidationError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid model response: {exc}") from exc

    return response


@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
