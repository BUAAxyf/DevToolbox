from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from devtoolbox.services.json_service import format_text, repair_text
from devtoolbox.services.text_diff_service import compare_texts

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="DevToolbox", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class JsonTextRequest(BaseModel):
    text: str


class JsonTextResponse(BaseModel):
    repaired: str
    formatted: str
    valid: bool
    error: str | None = None


class TextDiffRequest(BaseModel):
    left_text: str
    right_text: str
    left_name: str | None = None
    right_name: str | None = None
    markdown_render: bool = False


class DiffStatsResponse(BaseModel):
    added: int
    deleted: int
    modified: int
    same: int


class DiffRowResponse(BaseModel):
    kind: str
    left_no: int | None = None
    right_no: int | None = None
    left: str = ""
    right: str = ""


class TextDiffResponse(BaseModel):
    schema_version: str
    mode: str
    left_name: str
    right_name: str
    rows: list[DiffRowResponse]
    stats: DiffStatsResponse
    left_rendered_html: str | None = None
    right_rendered_html: str | None = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/tools/json")
def json_tool() -> FileResponse:
    return FileResponse(STATIC_DIR / "json.html")


@app.get("/tools/text-diff")
def text_diff_tool() -> FileResponse:
    return FileResponse(STATIC_DIR / "text_diff.html")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/json/repair", response_model=JsonTextResponse)
def repair_json_text(payload: JsonTextRequest) -> JsonTextResponse:
    result = repair_text(payload.text)
    return JsonTextResponse(**asdict(result))


@app.post("/api/json/format", response_model=JsonTextResponse)
def format_json_text(payload: JsonTextRequest) -> JsonTextResponse:
    result = format_text(payload.text)
    return JsonTextResponse(**asdict(result))


@app.post("/api/text-diff/compare", response_model=TextDiffResponse)
def compare_text(payload: TextDiffRequest) -> TextDiffResponse:
    result = compare_texts(
        left_text=payload.left_text,
        right_text=payload.right_text,
        left_name=payload.left_name,
        right_name=payload.right_name,
        markdown_render=payload.markdown_render,
    )
    return TextDiffResponse(**asdict(result))


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DevToolbox local web server.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Default: 127.0.0.1")
    parser.add_argument("--port", default=8000, type=int, help="Bind port. Default: 8000")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn auto-reload.")
    return parser.parse_args(argv)


def run_cli(
    argv: list[str] | None = None,
    *,
    runner: Callable[..., Any] | None = None,
) -> None:
    import uvicorn

    args = parse_cli_args(argv)
    uvicorn_runner = runner or uvicorn.run
    uvicorn_runner(
        "devtoolbox.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    run_cli()
