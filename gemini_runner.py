"""
gemini_runner.py

Shared Gemini / Google ADK execution wrapper.

PURPOSE
  Thin, reusable wrapper around Google ADK and the Gemini model family.
  Provides a GeminiRunner class that keeps all model interaction logic in
  one place so orchestrators stay focused on domain logic (prompts,
  personas, inputs, outputs).

INPUTS
  Environment variables (all optional if passed to constructor):
    GOOGLE_CLOUD_PROJECT   GCP project ID (required at instantiation)
    GOOGLE_CLOUD_LOCATION  GCP region (default: us-central1)
    GEMINI_MODEL           Model ID override (default: gemini-2.5-pro)

  Constructor arguments (keyword-only):
    agent_name      str   Logical agent name for ADK session routing
    instruction     str   System instruction / persona text
    model           str   Gemini model ID (overrides GEMINI_MODEL env var)
    vertex_project  str   GCP project ID (overrides GOOGLE_CLOUD_PROJECT)
    vertex_location str   GCP region (overrides GOOGLE_CLOUD_LOCATION)
    tools           list  ADK tool objects to attach to the agent
    use_search      bool  If True, attaches Google Search tool (UA/ESA stage 3)
    app_name        str   ADK application name for session scoping
    user_id         str   ADK session user identifier
    session_id      str   ADK session identifier

OUTPUTS
  str -- model response text, stripped of leading/trailing whitespace.
  Returns "No response returned." if the model produces no output.

DEPENDENCIES
  Internal : none
  External : google-adk, google-genai
             Install: pip install google-adk google-genai

USAGE
  from gemini_runner import GeminiRunner

  runner = GeminiRunner(
      agent_name="policy_reviewer",
      instruction="You are a security policy expert...",
      vertex_project="my-gcp-project",
  )

  # Synchronous (safe from any context)
  response = runner.ask("Review this policy section: ...")

  # Async (inside an async function)
  response = await runner.ask_async("Review this policy section: ...")

NOTES
  - Constructor raises EnvironmentError immediately if GOOGLE_CLOUD_PROJECT
    is not set -- fail fast rather than failing mid-run.
  - ask() handles event-loop detection automatically. When called inside a
    running async loop it spawns a ThreadPoolExecutor to avoid deadlock.
    For tight loops inside async code, prefer ask_async() directly.
  - Session state is maintained across multiple ask() calls on the same
    GeminiRunner instance, enabling multi-turn conversations.
  - This file must not contain domain logic. Orchestrators own all prompts,
    personas, file I/O, and output formatting.

DESIGN RULES
  No document parsing / No domain logic / No environment mutation /
  No hardcoded values
"""

from __future__ import annotations

import asyncio
import os
from typing import List, Optional

try:
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
except ImportError as e:
    raise RuntimeError(
        "google-adk and google-genai are required but not available. "
        "Run: pip install google-adk google-genai\n"
        f"Original error: {e}"
    ) from e


class GeminiRunner:
    """
    Shared Gemini / ADK execution wrapper.

    All orchestrators use this class directly. It must not be modified
    to support any single orchestrator's domain logic.

    Parameters
    ----------
    agent_name : str
        Logical name for the agent (used by ADK session routing).
    instruction : str
        System instruction / persona. Owned by the calling orchestrator.
    model : str
        Gemini model ID. Defaults to GEMINI_MODEL env var, then "gemini-2.5-pro".
    vertex_project : str, optional
        GCP project ID. Defaults to GOOGLE_CLOUD_PROJECT env var.
    vertex_location : str, optional
        GCP region. Defaults to GOOGLE_CLOUD_LOCATION env var, then "us-central1".
    tools : list, optional
        ADK tool objects to attach to the agent (e.g. function tools).
    use_search : bool
        If True, attaches Google Search as a tool (used by ua_esa stage 3).
    app_name : str
        ADK application name for session scoping.
    user_id : str
        ADK session user identifier.
    session_id : str
        ADK session identifier.
    """

    def __init__(
        self,
        *,
        agent_name: str,
        instruction: str,
        model: Optional[str] = None,
        vertex_project: Optional[str] = None,
        vertex_location: Optional[str] = None,
        tools: Optional[List] = None,
        use_search: bool = False,
        app_name: str = "GeminiRunner",
        user_id: str = "local_user",
        session_id: str = "default",
    ) -> None:
        self.agent_name = agent_name
        self.instruction = instruction
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        self.vertex_project = vertex_project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.vertex_location = vertex_location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.app_name = app_name
        self.user_id = user_id
        self.session_id = session_id

        resolved_tools: List = list(tools or [])
        if use_search:
            resolved_tools.append(
                types.Tool(google_search=types.GoogleSearch())
            )

        if self.vertex_project is None:
            raise EnvironmentError(
                "GOOGLE_CLOUD_PROJECT is not set. "
                "Set it in .env or pass vertex_project= to GeminiRunner."
            )

        self._agent = Agent(
            name=self.agent_name,
            model=self.model,
            instruction=self.instruction,
            tools=resolved_tools,
        )

        self._session_service = InMemorySessionService()

        self._runner = Runner(
            agent=self._agent,
            session_service=self._session_service,
            app_name=self.app_name,
        )

    async def _ensure_session(self) -> None:
        """Create the in-memory session on first use."""
        try:
            await self._session_service.get_session(
                user_id=self.user_id,
                session_id=self.session_id,
            )
        except Exception:
            await self._session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session_id,
            )

    async def ask_async(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and return the text response.

        Uses ADK Runner event streaming. Maintains session state across
        multiple calls on the same GeminiRunner instance, enabling
        multi-turn conversations.

        Parameters
        ----------
        prompt : str
            The user message to send.

        Returns
        -------
        str
            The model's text response, stripped of leading/trailing whitespace.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        await self._ensure_session()

        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        )

        events = self._runner.run_async(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=content,
        )

        final_parts: List[str] = []
        async for event in events:
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if getattr(part, "text", None):
                            final_parts.append(part.text)
                break

        return "".join(final_parts).strip() if final_parts else "No response returned."

    def ask(self, prompt: str) -> str:
        """
        Synchronous wrapper around ask_async().

        Safe to call from non-async orchestrators (policy, nfr, ua_esa).
        Handles event-loop detection automatically so callers do not need
        to manage asyncio themselves.

        Note: when called inside a running event loop this method spawns
        a ThreadPoolExecutor to avoid deadlock. For performance-sensitive
        code inside async functions use ask_async() directly instead.

        Parameters
        ----------
        prompt : str
            The user message to send.

        Returns
        -------
        str
            The model's text response.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, self.ask_async(prompt))
                return future.result()

        return asyncio.run(self.ask_async(prompt))
