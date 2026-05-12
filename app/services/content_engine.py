import hashlib
import random
from dataclasses import dataclass

from app.schemas.content import FollowUpContext, FollowUpQuestion, GeneratedPost, PostMetadata, QualityValidationResult
from app.services.content_memory import ContentMemory


HOOKS = [
    "A quiet failure taught me more than the launch did.",
    "The fastest teams I know do one uncomfortable thing early.",
    "I used to think automation was about speed. That was too small.",
    "There is a strange tax hiding inside every manual workflow.",
    "The best engineering cultures are not obsessed with tools.",
    "One dashboard changed how our team made decisions.",
    "A customer complaint can be a product strategy memo in disguise.",
    "Shipping faster rarely starts with typing faster.",
    "The boring system usually wins.",
    "This is where many SaaS teams accidentally slow themselves down.",
]

CTAS = [
    "What would you automate first in this workflow?",
    "I am curious where you draw the line between human judgment and automation.",
    "Save this for your next planning session.",
    "If your team has solved this differently, I would love to compare notes.",
    "Which part of this would be hardest to adopt in your org?",
    "Try one small version of this this week, then measure the drag it removes.",
    "What signal would convince you this is worth building?",
]

FORMATS = [
    "short_reflection",
    "numbered_breakdown",
    "mini_case_study",
    "contrast_lesson",
    "technical_steps",
    "myth_reframe",
    "narrative_arc",
]

TONES = [
    "practical and calm",
    "direct and opinionated",
    "warm and reflective",
    "technical but human",
    "sharp and executive",
    "curious and experimental",
]


@dataclass(frozen=True)
class PatternChoice:
    hook: str
    cta: str
    structure: str
    tone: str


class ContentEngine:
    def __init__(self, memory: ContentMemory | None = None) -> None:
        self.memory = memory or ContentMemory()

    async def build_follow_up_questions(self, context: FollowUpContext) -> list[FollowUpQuestion]:
        questions: list[FollowUpQuestion] = []
        if not context.target_audience:
            questions.append(FollowUpQuestion(key="target_audience", question="Who should this post speak to most directly?", reason="Audience changes vocabulary, examples, and CTA."))
        if not context.tone:
            questions.append(FollowUpQuestion(key="tone", question="What tone should it carry: practical, bold, reflective, technical, or founder-like?", reason="Tone prevents generic LinkedIn voice."))
        if not context.topic_depth:
            questions.append(FollowUpQuestion(key="topic_depth", question="Should this be a high-level insight, tactical playbook, or deep technical breakdown?", reason="Depth determines structure and jargon level."))
        if not context.platform_goal:
            questions.append(FollowUpQuestion(key="platform_goal", question="What is the goal: authority, leads, hiring, engagement, product education, or community trust?", reason="Goal shapes the CTA and framing."))
        if not context.desired_emotional_impact:
            questions.append(FollowUpQuestion(key="desired_emotional_impact", question="What should readers feel after reading it?", reason="Emotional target helps avoid robotic content."))
        if not context.image_style:
            questions.append(FollowUpQuestion(key="image_style", question="What image style fits: clean SaaS visual, editorial illustration, product mockup, diagram, or cinematic workspace?", reason="Image prompt needs a visual direction."))
        if not context.branding_preference:
            questions.append(FollowUpQuestion(key="branding_preference", question="Any brand colors, motifs, or visual constraints to include or avoid?", reason="Keeps generated assets brand-safe."))
        if not context.cta_preference:
            questions.append(FollowUpQuestion(key="cta_preference", question="Should the CTA invite comments, saves, DMs, signups, or a softer reflection?", reason="CTA repetition is one of the easiest ways content becomes templated."))
        return questions[:5]

    async def generate(self, request: FollowUpContext) -> GeneratedPost:
        memory = await self.memory.load()
        choice = self._choose_patterns(memory, request)
        content = self._compose_post(request, choice)
        title = self._title(request, choice)
        hashtags = self._hashtags(request)
        image_prompt = self._image_prompt(request, choice)
        fingerprint = self._fingerprint(content)
        await self.memory.append(
            {
                "openings": choice.hook,
                "ctas": choice.cta,
                "formats": choice.structure,
                "styles": request.preferred_style.value if request.preferred_style else choice.structure,
                "fingerprints": fingerprint,
            }
        )
        return GeneratedPost(
            title=title,
            content=content,
            hashtags=hashtags,
            image_prompt=image_prompt,
            style=request.preferred_style.value if request.preferred_style else choice.structure,
            tone=request.tone or choice.tone,
            metadata={"pattern": choice.__dict__, "fingerprint": fingerprint},
        )

    async def metadata(self, post: GeneratedPost) -> PostMetadata:
        fingerprint = self._fingerprint(post.content)
        structure = "list" if "\n1." in post.content else "compact" if post.content.count("\n") < 4 else "narrative"
        warnings = []
        banned = ["Most people", "Here’s the truth", "Nobody talks about", "I realized"]
        for phrase in banned:
            if post.content.startswith(phrase):
                warnings.append(f"Starts with discouraged phrase: {phrase}")
        return PostMetadata(
            estimated_read_time_seconds=max(10, round(len(post.content.split()) / 3.5)),
            character_count=len(post.content),
            hashtag_count=len(post.hashtags),
            detected_structure=structure,
            style_fingerprint=fingerprint,
            content_warnings=warnings,
        )

    async def validate_quality(self, post: GeneratedPost) -> QualityValidationResult:
        issues: list[str] = []
        suggestions: list[str] = []
        banned_openings = ("Most people", "Here’s the truth", "Nobody talks about", "I realized")
        if post.content.startswith(banned_openings):
            issues.append("Post starts with a discouraged repeated hook pattern.")
        if len(set(post.hashtags)) != len(post.hashtags):
            issues.append("Duplicate hashtags detected.")
        if post.content.count("\n\n") > 10:
            suggestions.append("Consider tightening paragraph breaks.")
        if any(word in post.content.lower() for word in ["unlock", "game-changing", "revolutionize", "leverage synergy"]):
            suggestions.append("Replace common AI-marketing phrasing with concrete language.")
        score = 1.0 - min(0.7, len(issues) * 0.25 + len(suggestions) * 0.1)
        return QualityValidationResult(passed=not issues and score >= 0.75, score=score, issues=issues, suggestions=suggestions)

    def _choose_patterns(self, memory: dict, request: FollowUpContext) -> PatternChoice:
        rng = random.SystemRandom()
        hook_pool = [item for item in HOOKS if item not in memory.get("openings", [])[-12:]] or HOOKS
        cta_pool = [item for item in CTAS if item not in memory.get("ctas", [])[-12:]] or CTAS
        format_pool = [item for item in FORMATS if item not in memory.get("formats", [])[-8:]] or FORMATS
        tone_pool = [request.tone] if request.tone else TONES
        return PatternChoice(rng.choice(hook_pool), rng.choice(cta_pool), rng.choice(format_pool), rng.choice(tone_pool))

    def _compose_post(self, request: FollowUpContext, choice: PatternChoice) -> str:
        audience = request.target_audience or "builders and operators"
        depth = request.topic_depth or "practical"
        goal = request.platform_goal or "start a useful conversation"
        emotion = request.desired_emotional_impact or "clear and energized"
        topic = request.topic.strip()
        if choice.structure == "numbered_breakdown":
            body = f"{choice.hook}\n\nFor {audience}, {topic} becomes real in three places:\n\n1. The handoff nobody owns\n2. The decision that waits for perfect data\n3. The repeat task people have learned to tolerate\n\nThe {depth} move is to automate the repeatable part and keep judgment visible where risk is high.\n\nThat is how automation earns trust instead of creating noise.\n\n{choice.cta}"
        elif choice.structure == "mini_case_study":
            body = f"{choice.hook}\n\nA team working on {topic} had a familiar problem: smart people, decent tools, and too many invisible steps between idea and outcome.\n\nThey did not need a bigger process. They needed one reliable loop:\n\nCapture the signal.\nRoute the decision.\nMake the next action obvious.\n\nThe result was not magic. It was less waiting, fewer status checks, and more energy for the work that actually needed taste.\n\n{choice.cta}"
        elif choice.structure == "technical_steps":
            body = f"{choice.hook}\n\nIf I were designing {topic} for {audience}, I would keep the architecture simple:\n\n- one source of truth for context\n- one generation layer with style memory\n- one validation pass before anything publishes\n- one integration boundary for approvals and APIs\n\nThe important part is not the model call. It is the control system around the model.\n\nThat is what makes the output feel consistent without becoming repetitive.\n\n{choice.cta}"
        elif choice.structure == "myth_reframe":
            body = f"{choice.hook}\n\nThe myth: {topic} is mainly about adopting better software.\n\nThe reality: it is about removing the tiny delays that make good teams feel slower than they are.\n\nFor {audience}, the win is not replacing people. It is giving people fewer stale decisions to drag around.\n\nThat is a different emotional outcome: {emotion}, not merely busy.\n\n{choice.cta}"
        else:
            body = f"{choice.hook}\n\n{topic} is easy to discuss as a strategy and surprisingly hard to practice on a normal Tuesday.\n\nThe teams that make it work usually do something simple: they decide what should be repeatable, what should be reviewed, and what should stay intentionally human.\n\nThat distinction protects quality while still creating speed.\n\nFor {audience}, that is often the difference between automation theater and actual operating leverage.\n\nThe goal is not to look advanced. The goal is to {goal}.\n\n{choice.cta}"
        return body

    def _title(self, request: FollowUpContext, choice: PatternChoice) -> str:
        seed = request.topic.strip().rstrip(".")
        prefixes = ["A practical note on", "How to rethink", "The hidden operating layer behind", "Building a better loop for", "What strong teams understand about"]
        return f"{random.SystemRandom().choice(prefixes)} {seed}"[:140]

    def _hashtags(self, request: FollowUpContext) -> list[str]:
        base = ["#LinkedIn", "#BuildInPublic"]
        topic = request.topic.lower()
        if "ai" in topic or "automation" in topic:
            base.extend(["#AIAutomation", "#WorkflowAutomation"])
        if "saas" in topic or "startup" in topic:
            base.extend(["#SaaS", "#StartupGrowth"])
        if "engineering" in topic or "developer" in topic:
            base.extend(["#EngineeringLeadership", "#DeveloperProductivity"])
        return base[:6]

    def _image_prompt(self, request: FollowUpContext, choice: PatternChoice) -> str:
        style = request.image_style or "clean editorial SaaS illustration"
        brand = request.branding_preference or "modern neutral palette with one confident accent color"
        return (
            f"{style} for a LinkedIn post about {request.topic}. "
            f"Visual metaphor: structured workflow becoming clearer without looking robotic. "
            f"Audience: {request.target_audience or 'technology leaders'}. "
            f"Branding: {brand}. No readable text, no logos, professional 16:9 composition."
        )

    def _fingerprint(self, content: str) -> str:
        normalized = " ".join(content.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
