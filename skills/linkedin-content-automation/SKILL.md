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
   Hint: cinematic workspace, clean SaaS diagram, product mockup, editorial illustration, dashboard-style visual.

7. Any branding preference?
   Hint: dark premium, blue/white, minimal neutral, CodeHills branding, no brand colors.

8. What CTA should it use?
   Hint: ask a question, invite DMs, book a call, save/share, soft reflection, no direct CTA.

## Generation Rules

After the user answers, generate:

- a unique LinkedIn title
- a unique LinkedIn post
- relevant hashtags
- a strong image prompt
- an image from that image prompt

Avoid repetitive AI-style writing. Vary hooks, CTA style, paragraph rhythm, storytelling structure, sentence length, and emotional style. Do not default to openings like "Most people...", "Here's the truth...", "Nobody talks about...", or "I realized...".

## MCP Workflow

After generating the post and image, run the MCP workflow. Do not stop after writing the post.

1. `validate_post_quality`
2. `generate_post_metadata`
3. `save_generated_post`
4. `upload_image_file` using the generated image path
5. `send_to_custom_api` using the returned image URL
6. `publish_to_linkedin` only if the user explicitly approves publishing

If image generation is unavailable, still generate the image prompt and explain that image upload cannot run without an actual image file.

If one MCP step fails, report the failure and continue with later steps that still make sense. Example: if custom API forwarding fails, still report validation, metadata, save, and image upload results.

## Image Rule

Always prefer `upload_image_file` for generated images.

Use `upload_generated_image` only when there is a real base64 payload from actual image bytes. Never invent placeholder base64 and never upload a tiny test image as if it were the generated image.

## Publishing Rule

Never publish directly to LinkedIn unless the user explicitly approves publishing in that same workflow.
