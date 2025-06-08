from typing import Any, Dict, TYPE_CHECKING
import time, logging

from .base_executor import BaseExecutor, ExecutorResult
from .utils import get_input_values, substitute_variables
from .validator import (
    validate_required_fields, validate_positive_integer,
    validate_either_required, validate_enum_field
)
from ...utils.token_usage import TokenUsage
from ...services.llm_service import LLMService
from ...utils.dependencies import get_memory_service
from ...utils.output_processor import OutputProcessor

if TYPE_CHECKING:
    from ..types import Ctx
    from .validator import ValidationResult

logger = logging.getLogger(__name__)

class PersonJobExecutor(BaseExecutor):
    def __init__(self, llm_service: LLMService):
        super().__init__()
        self.llm = llm_service

    async def validate(self, node: Dict[str, Any], context: 'Ctx') -> 'ValidationResult':
        props = node.get("properties", {})
        person = props.get("person") or getattr(context, 'persons', {}).get(props.get("personId"), {})
        errors = []
        # person/personId requirement
        errors += validate_either_required(props, [["person","personId"]], ["Provide person config or personId"])
        if not person and props.get("personId"):
            errors.append(f"Person '{props['personId']}' not found")
        if person:
            # required apiKeyId
            errors += validate_required_fields(person, ["apiKeyId"], {"apiKeyId": "API key ID"})
            # model name
            if not (person.get("modelName") or person.get("model")):
                errors.append("Model name is required in person config")
            # service enum
            if err := validate_enum_field(person, "service", ["openai","claude","gemini","grok"], case_sensitive=True):
                errors.append(err.replace("Invalid", "Unsupported"))
        # prompt requirement
        errors += validate_either_required(props, [["prompt","defaultPrompt"]], ["Provide prompt or defaultPrompt"])
        # maxIteration positive int
        if err := validate_positive_integer(props, "maxIteration", min_value=1, required=False):
            errors.append(err)
        return ValidationResult(is_valid=not errors, errors=errors, warnings=[])

    async def execute(self, node: Dict[str, Any], context: 'Ctx') -> ExecutorResult:
        start = time.time()
        props = node.get("properties", {})
        nid = node.get("id", "")
        count = context.exec_cnt.get(nid, 0)
        max_it = props.get("maxIteration")

        # skip if reached maxIteration
        if max_it and count >= max_it:
            last = context.outputs.get(nid, "No previous output")
            return ExecutorResult(
                output=last,
                metadata={"skipped": True, "reason": f"Max iterations ({max_it}) reached", "execution_count": count, "passthrough": True},
                tokens=TokenUsage(),
                execution_time=time.time() - start
            )

        # choose prompt
        prompt = (props.get("firstOnlyPrompt") if count == 0 and props.get("firstOnlyPrompt")
                  else props.get("defaultPrompt") or props.get("prompt", ""))
        if not prompt:
            return ExecutorResult(None, error="No prompt available", metadata={"execution_count": count}, tokens=TokenUsage(), execution_time=time.time() - start)

        # inputs & final prompt
        handler = "first" if count == 0 else "default"
        inputs = get_input_values(node, context, target_handle_filter=handler)
        final = substitute_variables(prompt, inputs)

        # person config
        person = props.get("person") or getattr(context, 'persons', {}).get(props.get("personId"), {})
        model = person.get("modelName") or person.get("model")
        key = person.get("apiKeyId")
        sys_p = person.get("systemPrompt", "")
        pid = person.get("id", nid)
        
        # Get service from API key
        svc = "openai"  # default service
        if key:
            try:
                from ...utils.app_context import app_context
                api_key_info = app_context.api_key_service.get_api_key(key)
                svc = api_key_info.get("service", "openai")
            except Exception as e:
                logger.warning(f"Failed to get API key info for {key}: {e}")
                # Fall back to default service

        # memory cleanup
        mem = get_memory_service()
        rule = props.get("contextCleaningRule", "no_forget")
        if mem and rule != "no_forget":
            if rule == "on_every_turn":
                mem.forget_for_person(pid)
            else:
                mem.forget_own_messages_for_person(pid, getattr(context, 'execution_id', None))

        # build messages
        history = mem.get_conversation_history(pid) if mem else []
        conv_inputs = []
        for arrow in context.graph.incoming.get(nid, []):
            # Check if arrow has content type (arrows might not have data in new structure)
            if arrow.label == "conversation_state" or arrow.t_handle == "conversation_state":
                out = context.outputs.get(arrow.source)
                if OutputProcessor.is_personjob_output(out):
                    conv_inputs += OutputProcessor.extract_conversation_history(out) or []
                    val = OutputProcessor.extract_value(out)
                    if val:
                        conv_inputs.append({"role": "user", "content": val})
        messages = history + conv_inputs + [{"role": "user", "content": final}]

        # interactive
        if props.get("interactive") and getattr(context, 'interactive_handler', None):
            resp = await context.interactive_handler(
                node_id=nid,
                prompt=final,
                context={"person_id": pid, "person_name": props.get("label", person.get("name", "Person")), "model": model, "service": svc, "execution_count": count}
            )
            if resp:
                messages.append({"role": "user", "content": resp})
                final += f"\n\nUser response: {resp}"

        # call LLM
        logger.debug(f"PersonJob {nid} exec #{count}")
        resp = await self.llm.call_llm(service=svc, api_key_id=key, model=model, messages=messages, system_prompt=sys_p)
        elapsed = time.time() - start
        usage = TokenUsage.from_response(resp)

        # store memory
        execution_id = getattr(context, 'execution_id', None)
        if execution_id and mem:
            mem.add_message_to_conversation(content=final, sender_person_id="user", execution_id=execution_id, participant_person_ids=[pid], role="user", node_id=nid, node_label=props.get("label", "PersonJob"))
            mem.add_message_to_conversation(content=resp["response"], sender_person_id=pid, execution_id=execution_id, participant_person_ids=[pid], role="assistant", node_id=nid, node_label=props.get("label", "PersonJob"), token_count=usage.total, input_tokens=usage.input, output_tokens=usage.output, cached_tokens=usage.cached)

        # build output
        out = OutputProcessor.create_personjob_output_from_tokens(
            text=resp["response"], token_usage=usage, conversation_history=messages[:-1], model=model, execution_time=elapsed
        )
        context.exec_cnt[nid] = count + 1

        return ExecutorResult(
            output=out,
            metadata={"person_id": pid, "service": svc, "model": model, "prompt_length": len(final), "system_prompt_length": len(sys_p), "execution_count": count+1, "used_first_only": count == 0 and bool(props.get("firstOnlyPrompt")), "executionTime": elapsed},
            tokens=usage,
            execution_time=elapsed
        )

class PersonBatchJobExecutor(PersonJobExecutor):
    async def validate(self, node: Dict[str, Any], context: 'Ctx') -> 'ValidationResult':
        res = await super().validate(node, context)
        if err := validate_positive_integer(node.get("properties", {}), "batchSize", min_value=1, required=False):
            res.errors.append(err)
            res.is_valid = not res.errors
        return res

    async def execute(self, node: Dict[str, Any], context: 'Ctx') -> ExecutorResult:
        res = await super().execute(node, context)
        props = node.get("properties", {})
        res.metadata.update({"node_type": "person_batch_job", "batch_size": props.get("batchSize", 1), "is_batch": True})
        return res
