"""LLM-based decision making adapter."""

import logging
import re
from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated.domain_models import PersonID, PersonLLMConfig
from dipeo.diagram_generated.enums import ExecutionPhase
from dipeo.domain.conversation import Person
from dipeo.infrastructure.llm.drivers.types import DecisionOutput

if TYPE_CHECKING:
    from dipeo.application.execution.orchestrators.execution_orchestrator import (
        ExecutionOrchestrator,
    )

logger = logging.getLogger(__name__)


class LLMDecisionAdapter:
    """LLM-based adapter for binary decision making using natural language prompts."""

    def __init__(self, orchestrator: "ExecutionOrchestrator"):
        self._orchestrator = orchestrator
        self._facet_cache: dict[str, Person] = {}

    def _decision_facet_id(self, person_id: PersonID) -> PersonID:
        return PersonID(f"{person_id!s}.__decision")

    def _decision_system_prompt(self, base_prompt: str | None) -> str:
        base = (base_prompt or "").strip()
        return (
            (base + "\n\n" if base else "") + "You are in DECISION MODE.\n"
            "- Evaluate the provided context and make a binary decision.\n"
            "- If the system supports structured output, provide:\n"
            "  - decision: true for YES/affirmative/valid/approved\n"
            "  - decision: false for NO/negative/invalid/rejected\n"
            "- Otherwise, respond with YES or NO at the start, followed by optional explanation.\n"
            "- Be decisive and clear in your judgment."
        )

    def _get_or_create_decision_facet(
        self, person_id: PersonID, diagram: Any | None = None
    ) -> Person:
        facet_id = self._decision_facet_id(person_id)
        persons = self._orchestrator.get_all_persons()
        if facet_id in persons:
            return persons[facet_id]

        base_person = self._orchestrator.get_or_create_person(person_id, diagram=diagram)
        llm = base_person.llm_config

        facet_cfg = PersonLLMConfig(
            service=llm.service,
            model=llm.model,
            api_key_id=llm.api_key_id,
            system_prompt=self._decision_system_prompt(llm.system_prompt),
            prompt_file=None,
        )

        facet = self._orchestrator.get_or_create_person(
            person_id=facet_id, name=f"{base_person.name} (Decision)", llm_config=facet_cfg
        )

        self._facet_cache[str(facet_id)] = facet
        return facet

    async def make_decision(
        self,
        person_id: PersonID,
        prompt: str,
        template_values: dict[str, Any] | None = None,
        memory_profile: str = "GOLDFISH",
        diagram: Any | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        if not prompt or not prompt.strip():
            logger.error("Empty prompt provided for decision")
            return False, {"error": "Empty prompt"}

        facet = self._get_or_create_decision_facet(person_id, diagram=diagram)

        llm_service = self._orchestrator.get_llm_service()
        if not llm_service:
            logger.error("LLM service not available from orchestrator")
            return False, {"error": "LLM service not available"}

        complete_prompt = prompt
        if memory_profile == "GOLDFISH" and template_values:
            content_to_evaluate = None

            if "default" in template_values:
                content_to_evaluate = template_values["default"]
                logger.debug("Using 'default' key as evaluation content")
            elif "generated_output" in template_values:
                content_to_evaluate = template_values["generated_output"]
                logger.debug("Using 'generated_output' key as evaluation content")
            else:
                context_keys = {
                    "current_index",
                    "last_index",
                    "iteration_count",
                    "loop_index",
                    "execution_count",
                    "node_execution_count",
                }
                filtered = {}
                for k, v in template_values.items():
                    if (
                        not k.startswith("branch[")
                        and not k.endswith("_last_increment_at")
                        and k not in context_keys
                    ):
                        filtered[k] = v

                if filtered:
                    content_to_evaluate = filtered
                    logger.debug(f"Using filtered content with {len(filtered)} keys")
                else:
                    content_to_evaluate = template_values
                    logger.debug("Using all template values as fallback")

            if content_to_evaluate is not None:
                import json

                if isinstance(content_to_evaluate, str):
                    complete_prompt = f"{prompt}\n\n--- Content to Evaluate ---\n{content_to_evaluate}\n--- End of Content ---"
                else:
                    try:
                        content_json = json.dumps(content_to_evaluate, indent=2)
                        complete_prompt = f"{prompt}\n\n--- Content to Evaluate ---\n{content_json}\n--- End of Content ---"
                    except (TypeError, ValueError) as e:
                        logger.warning(
                            f"Failed to serialize content to JSON: {e}. Using string representation."
                        )
                        complete_prompt = f"{prompt}\n\n--- Content to Evaluate ---\n{content_to_evaluate!s}\n--- End of Content ---"

        complete_kwargs = {
            "prompt": complete_prompt,
            "all_messages": [],
            "llm_service": llm_service,
            "temperature": 0,
            "max_tokens": 8000,
            "execution_phase": ExecutionPhase.DECISION_EVALUATION,
        }

        if template_values and "text_format" in template_values:
            text_format = template_values.pop("text_format")
            if isinstance(text_format, type) and hasattr(text_format, "__mro__"):
                complete_kwargs["text_format"] = text_format

        try:
            result, incoming_msg, response_msg = await facet.complete(**complete_kwargs)
            if hasattr(self._orchestrator, "add_message"):
                self._orchestrator.add_message(incoming_msg, "decision", "decision_maker")
                self._orchestrator.add_message(response_msg, "decision", "decision_maker")

            response_text = getattr(result, "content", getattr(result, "text", "")) or ""

            decision = False
            reasoning = None

            llm_response = result.raw_response if hasattr(result, "raw_response") else result

            if hasattr(llm_response, "structured_output") and llm_response.structured_output:
                structured = llm_response.structured_output

                if isinstance(structured, DecisionOutput):
                    decision = structured.decision
                elif hasattr(structured, "decision"):
                    decision = bool(structured.decision)
                    reasoning = getattr(structured, "reasoning", None)
                else:
                    decision = self._parse_text_decision(response_text)
            else:
                decision = self._parse_text_decision(response_text)

            if reasoning:
                logger.debug(
                    f"LLM Decision: {decision} (reasoning: {reasoning[:50] + '...' if len(reasoning) > 50 else reasoning})"
                )
            else:
                logger.debug(f"LLM Decision: {decision}")

            metadata = {
                "response": response_text,
                "response_preview": response_text[:200],
                "decision": decision,
                "person": str(person_id),
                "memory_profile": memory_profile,
            }

            if reasoning:
                metadata["reasoning"] = reasoning

            return decision, metadata

        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return False, {"error": str(e)}

    def _parse_text_decision(self, response_text: str) -> bool:
        if not response_text:
            return False

        response_stripped = response_text.strip()
        if response_stripped.startswith("{") and response_stripped.endswith("}"):
            try:
                import json

                json_data = json.loads(response_stripped)
                if "decision" in json_data:
                    return bool(json_data["decision"])
            except (json.JSONDecodeError, ValueError):
                pass

        response_lower = response_text.lower().strip()
        response_lower = re.sub(r"[*_`#\[\]()]", "", response_lower)

        if response_lower.startswith("yes"):
            return True
        if response_lower.startswith("no"):
            return False

        affirmative_keywords = [
            "yes",
            "true",
            "valid",
            "approved",
            "approve",
            "accept",
            "accepted",
            "correct",
            "pass",
            "passed",
            "good",
            "ok",
            "okay",
            "proceed",
            "continue",
            "affirmative",
            "positive",
            "success",
            "successful",
        ]

        negative_keywords = [
            "no",
            "false",
            "invalid",
            "rejected",
            "reject",
            "deny",
            "denied",
            "incorrect",
            "fail",
            "failed",
            "bad",
            "not ok",
            "not okay",
            "stop",
            "halt",
            "negative",
            "unsuccessful",
            "error",
            "wrong",
        ]

        affirmative_count = sum(1 for keyword in affirmative_keywords if keyword in response_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in response_lower)

        if affirmative_count > negative_count:
            return True
        elif negative_count > affirmative_count:
            return False

        logger.warning(f"Ambiguous LLM response for decision: {response_text[:100]}...")
        return False
