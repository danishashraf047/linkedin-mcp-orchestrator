---
name: linkedin-content-automation
description: Use when the user asks to create a LinkedIn post with MCP, generate a LinkedIn post and image, validate/save/forward a LinkedIn post package, or run the LinkedIn content automation workflow. Always includes follow-up questions, post generation, image generation/upload, MCP validation, metadata, saving, and custom API forwarding unless the user explicitly opts out.
metadata:
  short-description: LinkedIn post + MCP workflow
---

# LinkedIn Content Automation

## Core Rule

When the user asks to create a LinkedIn post, especially "with MCP", always ask follow-up questions first and include image generation in the workflow.

Do not generate the post, image prompt, image, or MCP calls until the user answers the follow-up questions, unless they explicitly say "do not ask follow-up questions" or "use the provided details only."

## Follow-Up Questions

Ask all eight questions together. Keep them concise, and include the hint for each question so the user can answer quickly.

1. Who is the target audience?
   Hint: SaaS founders, CTOs, support leaders, developers, RevOps, agency owners.

2. What tone should the post use?
   Hint: technical, practical, bold, founder-story, contrarian, warm, executive.

3. How deep should the topic go?
   Hint: high-level insight, tactical playbook, technical breakdown, case study, personal lesson.

4. What is the platform goal?
   Hint: start conversations, build authority, attract leads, educate buyers, promote a service, hire talent.

5. What should readers feel after reading?
   Hint: confidence, urgency, clarity, curiosity, relief, ambition.

6. What image style should accompany the post?
   Hint: default to the signature dark premium infographic theme: black/navy background, white title text, blue-magenta gradient emphasis, neon line icons, subtle network lines, and a glowing digital wave.

7. Any branding preference?
   Hint: default dark premium technology palette with white, electric blue, cyan, violet, and magenta accents.

8. What CTA should it use?
   Hint: ask a question, invite DMs, book a call, save/share, soft reflection, no direct CTA.

## Generation Rules

After the user answers, generate in this order:

- a unique LinkedIn title
- a unique LinkedIn post
- relevant hashtags
- a strong image prompt

Then validate the post content before generating any image. Generate the image only after the post passes validation.

Avoid repetitive AI-style writing. Vary hooks, CTA style, paragraph rhythm, storytelling structure, sentence length, and emotional style. Do not default to openings like "Most people...", "Here's the truth...", "Nobody talks about...", or "I realized...".

## Signature Image Theme

Unless the user explicitly asks for a different visual direction, generate every image in this theme:

- Square 1:1 LinkedIn post graphic.
- Near-black/navy background with subtle constellation or network lines.
- Glowing blue-to-magenta digital wave or dot field along the bottom.
- Large, readable, uppercase post title in white, with one key word in a blue-to-magenta gradient.
- Optional small spaced eyebrow text above the title and a short subtitle below it.
- One to four minimalist neon outline icons only when they clarify the topic.
- Thin neon dividers, high contrast, polished executive SaaS feel.

The image should include the post title when useful. Keep typography sharp and readable. Avoid logos, stock photography, clutter, and paragraphs of tiny text.

## MCP Workflow

After drafting the post content, run the MCP workflow. Do not generate the image until validation passes.

1. Draft the post package: title, content, hashtags, tone/style, and image prompt. Do not generate an image yet.
2. `validate_post_quality`
3. If validation fails, revise the post and validate again before any image generation.
4. `generate_post_metadata`
5. Generate exactly one raster image from the image prompt using the image generation tool.
6. `upload_image_file` using the original generated raster image path and keep the returned stored image `path`, `image.url`, and `source_path`
7. `save_generated_post` with the returned stored image `path`, `image.url`, and original generated raster image path, then keep the returned JSON `path`
8. Pause for human approval of both the saved JSON post and the saved image
9. `send_to_custom_api` using the returned `image.url`, saved JSON path, stored image path, and `approved=true`
10. Before publishing, ask whether to post as `personal` or `company`
11. `publish_to_linkedin` only if the user explicitly approves publishing, passing the saved JSON path, stored image path, `approved=true`, and the selected `post_as`

If image generation is unavailable, still generate the image prompt and explain that image upload cannot run without an actual image file.

If one MCP step fails, report the failure and continue with later steps that still make sense. Example: if custom API forwarding fails, still report validation, metadata, save, and image upload results.

Do not publish to LinkedIn if image generation, local image saving, or `upload_image_file` fails. Fix or regenerate the image first, then publish with `image_path`. Only publish text-only when the user explicitly approves a text-only post.

Do not send the draft package to the custom API unless `upload_image_file` succeeded and returned an `image.url`. Use that URL as `image_url`.

Do not send anything to the custom API or LinkedIn until the post exists as JSON in `storage/posts`, the image exists in `storage/images`, the saved JSON includes `metadata.approved_image`, and the user approves both artifacts.

The saved JSON approved image hash must match the stored image hash and the generated source image hash. If they do not match, stop and re-upload the correct generated image.

Never generate the image before `validate_post_quality` passes. This prevents wasting image generations on post drafts that still need revision.

## Image Rule

Always use the original raster image produced by image generation as the source of truth.

Do not create SVG, HTML, canvas, or React/CSS artwork for the LinkedIn image workflow. Do not use Playwright, browser screenshots, HTML-to-image, SVG-to-PNG, or any rendering/conversion workaround unless the user explicitly asks for that exact approach.

Do not regenerate the image after the first acceptable image is produced. Upload that exact file directly to MCP with `upload_image_file`.

Use `upload_generated_image` only when the image generation tool returns a real base64 payload from actual image bytes instead of a file path. Never invent placeholder base64 and never upload a tiny test image as if it were the generated image.

If the built-in image generation tool displays an image but does not show a path in the chat, look for the generated raster under `$CODEX_HOME/generated_images/` or `~/.codex/generated_images/` and use the newest matching PNG/JPEG/WebP from that folder as the source image. Do this before telling the user no usable path exists.

If no generated raster file exists under the built-in image output folder and the tool did not return real image bytes, stop and tell the user the image cannot be uploaded safely. Do not substitute a screenshot or recreated visual.

## Publishing Rule

Never publish directly to LinkedIn unless the user explicitly approves publishing in that same workflow.

Always ask where to publish before calling `publish_to_linkedin`: `personal` profile or `company` page.

When publishing, pass an `image_path`, `saved_post_path`, `approved=true`, and `post_as` by default. Use `post_as="personal"` for the member profile and `post_as="company"` for the company page. Company publishing requires `LINKEDIN_ORGANIZATION_URN` in `.env`. The publishing tool requires an image and saved artifacts unless `require_image=false` or `require_saved_artifacts=false` is explicitly set for a user-approved exception.
