# LinkedIn MCP Orchestrator

Production-ready Python 3.12 project for AI-assisted LinkedIn content workflows using FastAPI, MCP, Pydantic, async HTTP clients, local image storage, and optional LinkedIn publishing.

The workflow is:

1. Codex asks follow-up questions before writing.
2. Codex generates a unique LinkedIn post package: title, post, hashtags, image prompt, and image.
3. Codex calls the `linkedin-content-automation` MCP tools.
4. The MCP server validates quality, generates metadata, saves the post, uploads the generated image, and forwards the package to the custom API.
5. LinkedIn publishing only happens after explicit approval.

## Features

- Dynamic follow-up questions with hints for audience, tone, depth, goal, emotion, image style, branding, and CTA.
- Anti-repetition content engine that rotates hooks, structures, CTAs, tone, formatting, and content fingerprints.
- MCP tools for validation, metadata, persistence, image upload, custom API forwarding, and LinkedIn publishing.
- FastAPI routes for local API testing and custom API simulation.
- Local image storage with MIME checks and image byte validation, including PNG CRC validation.
- Async `httpx` custom API and LinkedIn clients with retries, timeouts, logging, and typed schemas.
- Docker support for FastAPI and MCP HTTP modes.
- Codex skill included under `skills/linkedin-content-automation`.

## Project Structure

```text
app/
  main.py                 FastAPI application
  mcp_server.py           MCP server entrypoint
  config.py               environment settings
  api/routes.py           HTTP routes
  schemas/                Pydantic request/response models
  services/               content engine, API client, storage, memory
  tools/mcp_tools.py      MCP tool implementations
  linkedin/client.py      LinkedIn REST API integration
  prompts/                prompt guidance
  utils/                  logging, retry, image validation helpers
skills/
  linkedin-content-automation/SKILL.md
storage/
  images/                 generated/uploaded image files
  posts/                  saved generated post JSON files
Dockerfile
mcp_config.json
requirements.txt
.env.example
```

Runtime files inside `storage/images`, `storage/posts`, and `storage/content_history.json` are intentionally ignored by git.

## Setup With pyenv

```bash
cd /Users/danish/Documents/Projects/linkedin-mcp-orchestrator
pyenv install 3.12.9
pyenv local 3.12.9
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` for your local setup:

```env
CUSTOM_API_BASE_URL=http://localhost:8000
PUBLIC_BASE_URL=http://localhost:8000

LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_PERSON_URN=urn:li:person:YOUR_PERSON_ID
```

LinkedIn values are only required when you want to publish directly to LinkedIn.

## Run FastAPI

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Useful URLs:

- `http://localhost:8000/docs`
- `http://localhost:8000/api/health`
- `http://localhost:8000/images/<filename>`

## Run MCP

For Codex, run the MCP server over streamable HTTP:

```bash
source .venv/bin/activate
LINKEDIN_MCP_TRANSPORT=streamable-http \
FASTMCP_HOST=127.0.0.1 \
FASTMCP_PORT=8765 \
FASTMCP_STREAMABLE_HTTP_PATH=/mcp \
python -m app.mcp_server
```

The MCP endpoint will be:

```text
http://127.0.0.1:8765/mcp
```

For stdio MCP clients:

```bash
python -m app.mcp_server
```

## Codex Setup

Use this config in `~/.codex/config.toml`:

```toml
[mcp_servers.linkedin-content-automation]
url = "http://127.0.0.1:8765/mcp"
startup_timeout_sec = 20
tool_timeout_sec = 300
```

Restart Codex after changing MCP settings.

The project also includes a Codex skill at:

```text
skills/linkedin-content-automation/SKILL.md
```

The installed user skill should live at:

```text
~/.codex/skills/linkedin-content-automation/SKILL.md
```

That skill tells Codex to always ask follow-up questions first, generate both post and image, upload the actual generated image file through MCP, and avoid publishing to LinkedIn unless approved.

## MCP Tools

The `linkedin-content-automation` MCP server exposes:

- `validate_post_quality`
- `generate_post_metadata`
- `save_generated_post`
- `upload_image_file`
- `upload_generated_image`
- `send_to_custom_api`
- `publish_to_linkedin`

Preferred image flow:

1. Draft the post package first: title, content, hashtags, tone/style, and image prompt.
2. Call `validate_post_quality`.
3. If validation fails, revise the post and validate again before generating any image.
4. Generate the image once with Codex image generation only after validation passes.
5. Call `upload_image_file` with the original generated image path.
6. Call `save_generated_post` with the returned stored image path, `image.url`, and generated source image path.
7. Keep the returned JSON path and use the returned `image.url` in the custom API payload.
8. Review and approve both the saved JSON post and the saved image.
9. Send or publish only after approval, passing `saved_post_path`, the stored image path, and `approved=true`.

Use `upload_generated_image` only when the client already has real base64 image bytes. The server rejects corrupt image bytes before writing files.

Custom API sending and LinkedIn publishing require saved artifacts and approval by default. The saved JSON must include `metadata.approved_image`, and its image hash must match the stored image. To publish a text-only post, explicitly pass `require_image=false` after approval.

Do not use SVG, HTML, canvas, browser screenshots, Playwright, or conversion/rendering workarounds for the default LinkedIn image workflow. The approved image must be the original raster image produced by image generation and uploaded directly to MCP.

## Codex Workflow Prompt

Use a prompt like this:

```text
Create a LinkedIn post about AI automation for SaaS support teams with MCP.

Before writing, ask me follow-up questions about audience, tone, depth, goal, emotional impact, image style, branding, and CTA.

Use the signature image theme by default: a square dark premium LinkedIn infographic with a black/navy background, white title typography, blue-to-magenta gradient emphasis, subtle network lines, optional neon outline icons, and a glowing digital wave.

After I answer:
1. Generate a unique LinkedIn post.
2. Generate a title, hashtags, and image prompt.
3. Generate an image using the image prompt.
4. Use the linkedin-content-automation MCP server to:
   - validate_post_quality
   - generate_post_metadata
   - save_generated_post
   - upload_image_file
   - send_to_custom_api

Do not publish to LinkedIn unless I explicitly approve.
```

Example answers:

```text
SaaS founders
technical
technical breakdown
start conversations
confidence
cinematic workspace
dark premium
book a call
```

## Debug MCP Tool Calls

Use VS Code or Cursor:

1. Open this project.
2. Set breakpoints in `app/tools/mcp_tools.py`, `app/services/content_engine.py`, `app/services/image_storage.py`, or `app/linkedin/client.py`.
3. Run the launch target `MCP HTTP Debug Server`.
4. Confirm Codex is configured for `http://127.0.0.1:8765/mcp`.
5. Ask Codex to call an MCP tool.

There is no attach-to-port debugger in this project. The old `debugpy` attach flow was removed because Codex connects more reliably to the already-running HTTP MCP server.

## FastAPI Examples

Generate follow-up questions:

```bash
curl -X POST http://localhost:8000/api/content/follow-up-questions \
  -H "Content-Type: application/json" \
  -d '{"topic":"AI automation for SaaS support teams"}'
```

Generate a post package:

```bash
curl -X POST http://localhost:8000/api/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI automation for SaaS support teams",
    "target_audience": "SaaS founders",
    "tone": "technical but human",
    "topic_depth": "technical breakdown",
    "platform_goal": "start conversations",
    "desired_emotional_impact": "confidence",
    "image_style": "signature dark premium LinkedIn infographic",
    "branding_preference": "black/navy background, white text, electric blue, cyan, violet, and magenta accents",
    "cta_preference": "book a call"
  }'
```

Upload an image:

```bash
curl -X POST http://localhost:8000/api/images \
  -F "file=@/path/to/generated-image.png"
```

Forward a post to the custom API:

```bash
curl -X POST http://localhost:8000/api/integrations/custom-api \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Automation should keep judgment visible",
    "content": "Post content here",
    "hashtags": ["#AIAutomation", "#SaaS"],
    "image_url": "http://localhost:8000/images/example.png",
    "image_path": "storage/images/example.png",
    "saved_post_path": "storage/posts/example.json",
    "approved": true,
    "image_prompt": "Cinematic dark premium SaaS support workspace, no text",
    "platform": "linkedin",
    "author": "Danish",
    "tone": "technical but human",
    "metadata": {}
  }'
```

Publish to LinkedIn after approval:

```bash
curl -X POST http://localhost:8000/api/linkedin/publish \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Post content here",
    "image_path": "storage/images/example.png",
    "saved_post_path": "storage/posts/example.json",
    "approved": true,
    "require_image": true,
    "visibility": "PUBLIC"
  }'
```

## Docker

Build the image:

```bash
docker build -t linkedin-mcp-orchestrator .
```

Run FastAPI:

```bash
docker run --rm --env-file .env -p 8000:8000 linkedin-mcp-orchestrator
```

Run MCP HTTP:

```bash
docker run --rm --env-file .env \
  -e LINKEDIN_MCP_TRANSPORT=streamable-http \
  -e FASTMCP_HOST=0.0.0.0 \
  -e FASTMCP_PORT=8765 \
  -e FASTMCP_STREAMABLE_HTTP_PATH=/mcp \
  -p 8765:8765 \
  linkedin-mcp-orchestrator \
  python -m app.mcp_server
```

For local Codex debugging, the non-Docker VS Code `MCP HTTP Debug Server` flow is usually better because breakpoints work directly against your source files.

## Docker And Git Ignore Policy

The ignore files are configured so secrets and runtime artifacts stay out of images and source control:

- `.env` and `.env.*` are ignored.
- `.env.example` is kept.
- `.venv`, caches, `.DS_Store`, logs, and generated folders are ignored.
- Generated image/post outputs are ignored.
- `storage/images/.gitkeep` and `storage/posts/.gitkeep` preserve empty runtime directories.

## LinkedIn Notes

LinkedIn publishing uses LinkedIn REST APIs for posts and image upload initialization. Your LinkedIn app must have the correct products, scopes, member URN, and access token for posting. The MCP workflow will not publish unless `publish_to_linkedin` is explicitly called.

## Author

Danish Ashraf · danish.ashraf@codehills.net · https://codehills.net
