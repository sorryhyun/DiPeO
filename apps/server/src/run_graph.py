from __future__ import annotations
import re
import json
import asyncio
import logging
import time
from datetime import datetime
from .db_blocks import run_db_block
from collections import Counter, deque
from typing import Any, Dict, List, Tuple, Optional, Callable, Awaitable, Set
from dataclasses import dataclass
from .constants import NodeType
from .services.llm_service import LLMService
from .services.api_key_service import APIKeyService
from .services.memory_service import MemoryService
from .services.notion_service import NotionService
from .utils.resolve_utils import resolve_inputs, render_prompt
from .utils.personjob_utils import execute_personjob
from .utils.dynamic_executor import DynamicExecutor
from .utils.arrow_utils import ArrowUtils

# Structured logging and metrics
import structlog
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge

# Metrics
node_executions_total = PrometheusCounter(
    'node_executions_total', 
    'Total node executions', 
    ['node_type', 'status']
)
execution_duration_seconds = Histogram(
    'execution_duration_seconds', 
    'Node execution duration'
)
active_executions = Gauge(
    'active_executions', 
    'Number of active executions'
)
llm_cost_total = PrometheusCounter(
    'llm_cost_total', 
    'Total LLM cost in USD'
)

# Structured logger
logger = structlog.get_logger(__name__)


@dataclass
class ExecutionState:
    """Holds mutable state during diagram execution."""
    context: Dict[str, Any]
    condition_values: Dict[str, bool]
    counts: Counter
    total_cost: float
    node_max_iterations: Dict[str, int]


class NodeExecutor:
    """Handles execution of individual nodes."""
    
    def __init__(self, 
                 nodes: Dict[str, dict],
                 persons: Dict[str, dict],
                 llm_service: LLMService,
                 memory_service: MemoryService,
                 execution_id: str,
                 send_status_update_fn: Callable):
        self.nodes_by_id = nodes
        self.persons = persons
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.execution_id = execution_id
        self._send_status_update = send_status_update_fn
        
    async def execute_node(
            self,
            node: dict,
            vars_map: Dict[str, Any],
            inputs: List[Any],
            incoming_arrows: List[dict],
            state: ExecutionState
    ) -> Tuple[Any, float]:
        """Dispatch to the correct node‑type handler."""
        node_id = node.get("id")
        ntype_str = node.get("type")
        data = node.get("data", {})
        
        start_time = time.time()
        active_executions.inc()
        
        logger.info(
            "executing_node",
            node_id=node_id,
            node_type=ntype_str,
            execution_id=self.execution_id
        )
        
        try:
            ntype = NodeType.from_legacy(ntype_str)
        except ValueError:
            logger.warning("unknown_node_type", node_type=ntype_str, node_id=node_id)
            node_executions_total.labels(node_type=ntype_str, status="error").inc()
            active_executions.dec()
            return None, 0.0

        try:
            result = None
            cost = 0.0
            
            if ntype == NodeType.PERSON_JOB:
                person_id = data.get("personId")
                person = self.persons.get(person_id, {})
                result, cost = await self._execute_personjob(node, person, vars_map, incoming_arrows, state)

            elif ntype == NodeType.CONDITION:
                result, cost = self._execute_condition(node, vars_map, incoming_arrows, state)

            elif ntype == NodeType.DB:
                logger.debug("executing_db_node", node_id=node_id, data=data)
                result = await run_db_block(data, inputs)
                cost = 0.0

            elif ntype == NodeType.JOB:
                sub_type = data.get("subType", "code")
                if sub_type == "api_tool":
                    result = await self._execute_api_tool(data, inputs)
                else:
                    result = await run_db_block({"subType": "code", "sourceDetails": data.get("sourceDetails", "")}, inputs)
                cost = 0.0

            elif ntype == NodeType.ENDPOINT:
                # Handle endpoint blocks with optional file save
                if data.get("saveToFile") or data.get("filePath"):
                    result = await self._execute_endpoint_save(data, inputs)
                else:
                    # Just pass through the input if no file save
                    result = inputs[0] if inputs else None
                cost = 0.0
            
            # Record metrics
            execution_duration_seconds.observe(time.time() - start_time)
            node_executions_total.labels(node_type=ntype_str, status="success").inc()
            if cost > 0:
                llm_cost_total.inc(cost)
            
            logger.info(
                "node_completed", 
                node_id=node_id, 
                duration=time.time() - start_time,
                cost=cost
            )
            
            return result, cost
            
        except Exception as e:
            # Record error metrics
            execution_duration_seconds.observe(time.time() - start_time)
            node_executions_total.labels(node_type=ntype_str, status="error").inc()
            
            logger.error(
                "node_execution_failed",
                node_id=node_id,
                error=str(e),
                duration=time.time() - start_time
            )
            raise
        finally:
            active_executions.dec()
    
    async def _execute_personjob(
            self,
            node: dict,
            person: dict,
            vars_map: Dict[str, Any],
            incoming_arrows: List[dict],
            state: ExecutionState
    ) -> Tuple[Any, float]:
        """Execute person job node - delegates to utility function."""
        return await execute_personjob(
            node=node,
            person=person,
            vars_map=vars_map,
            incoming_arrows=incoming_arrows,
            counts=state.counts,
            context=state.context,
            memory_service=self.memory_service,
            llm_service=self.llm_service,
            execution_id=self.execution_id,
            arrow_src_fn=ArrowUtils.get_source,
            send_status_update_fn=self._send_status_update,
            get_all_person_ids_fn=self._get_all_person_ids_in_diagram
        )
    
    def _execute_condition(
            self,
            node: dict,
            vars_map: Dict[str, Any],
            incoming_arrows: List[dict],
            state: ExecutionState
    ) -> Tuple[Any, float]:
        data = node.get("data", {})
        node_id = node.get("id")
        condition_type = data.get("conditionType", "")
        
        if condition_type == "max_iterations":
            cond_flag = self._check_max_iterations(node_id, incoming_arrows, state)
        else:
            cond_flag = self._evaluate_expression(node_id, data.get("expression", ""), vars_map)
            
        if node_id is not None:
            state.condition_values[node_id] = cond_flag
            
        logger.debug(f"[Condition {node_id}] Evaluated to: {cond_flag}")
        
        if incoming_arrows:
            src_id = ArrowUtils.get_source(incoming_arrows[0])
            payload = state.context.get(src_id)
        else:
            payload = None
            
        return payload, 0.0
    
    def _check_max_iterations(self, node_id: str, incoming_arrows: List[dict], state: ExecutionState) -> bool:
        """Check if upstream node has reached max iterations."""
        if not incoming_arrows:
            return False
            
        upstream_id = ArrowUtils.get_source(incoming_arrows[0])
        logger.debug(f"[Condition {node_id}] Checking upstream node {upstream_id}")
        
        if upstream_id in state.node_max_iterations:
            max_iter = state.node_max_iterations[upstream_id]
            current_count = state.counts.get(upstream_id, 0)
            if current_count >= max_iter:
                return True
        
        upstream_context = state.context.get(upstream_id, {})
        if isinstance(upstream_context, dict) and upstream_context.get("skipped_max_iter"):
            return True
            
        return False
    
    def _evaluate_expression(self, node_id: str, expr: str, vars_map: Dict[str, Any]) -> bool:
        """Evaluate a condition expression."""
        if not expr:
            return False
            
        try:
            return bool(eval(expr, {}, vars_map))
        except Exception as ex:
            raise ValueError(f"Error evaluating condition at node {node_id}: {ex}")
    
    def _get_all_person_ids_in_diagram(self) -> List[str]:
        """Get all person IDs that have personjobNode in the current diagram."""
        person_ids = set()
        for node in self.nodes_by_id.values():
            try:
                node_type = NodeType.from_legacy(node.get("type", ""))
                if node_type == NodeType.PERSON_JOB:
                    person_id = node.get("data", {}).get("personId")
                    if person_id:
                        person_ids.add(person_id)
            except ValueError:
                pass
        return list(person_ids)
    
    async def _execute_endpoint_save(self, data: dict, inputs: List[Any]) -> Any:
        """Execute endpoint node with file save."""
        from .db_blocks import run_db_target_block
        
        # Convert to the format expected by run_db_target_block
        target_data = {
            "targetType": "local_file",
            "targetDetails": data.get("filePath", ""),
            "fileFormat": data.get("fileFormat", "text")
        }
        
        return await run_db_target_block(target_data, inputs)
    
    async def _execute_api_tool(self, data: dict, inputs: List[Any]) -> Any:
        """Execute API tool operations like Notion integration."""
        # Parse the sourceDetails JSON string to get the API configuration
        source_details = data.get("sourceDetails", "{}")
        logger.debug(f"[API Tool] Raw sourceDetails: {source_details}")
        
        try:
            api_config = json.loads(source_details) if isinstance(source_details, str) else source_details
        except json.JSONDecodeError:
            raise ValueError(f"Invalid API configuration JSON: {source_details}")
        
        logger.debug(f"[API Tool] Parsed config: {api_config}")
        api_type = api_config.get("apiType", "")
        logger.debug(f"[API Tool] API type: '{api_type}'")
        
        if api_type == "notion":
            notion_service = NotionService()
            action = api_config.get("action", "query_database")
            
            # Get API key from the prompts/notion.yaml file
            import yaml
            import os
            notion_yaml_path = os.path.join(os.path.dirname(__file__), "../../../prompts/notion.yaml")
            with open(notion_yaml_path, "r") as f:
                notion_config = yaml.safe_load(f)
                api_key = notion_config.get("token", "")
            
            if action == "query_database":
                database_id = api_config.get("databaseId", "")
                filter_obj = api_config.get("filter", None)
                sorts = api_config.get("sorts", None)
                
                if not database_id:
                    raise ValueError("Database ID is required for Notion query")
                
                result = await notion_service.query_database(
                    api_key=api_key,
                    database_id=database_id,
                    filter_obj=filter_obj,
                    sorts=sorts
                )
                return result
            
            elif action == "create_page":
                database_id = api_config.get("databaseId", "")
                properties = api_config.get("properties", {})
                
                # If inputs provided, use the first input as content
                if inputs and isinstance(inputs[0], str):
                    # Try to parse as JSON for properties
                    try:
                        properties = json.loads(inputs[0])
                    except:
                        # If not JSON, create a simple title property
                        properties = {
                            "Name": {
                                "title": [{"text": {"content": inputs[0]}}]
                            }
                        }
                
                result = await notion_service.create_page(
                    api_key=api_key,
                    parent_database_id=database_id,
                    properties=properties
                )
                return result
            
            elif action == "update_page":
                page_id = api_config.get("pageId", "")
                properties = api_config.get("properties", {})
                
                result = await notion_service.update_page(
                    api_key=api_key,
                    page_id=page_id,
                    properties=properties
                )
                return result
            
            elif action == "search":
                query = api_config.get("query", "")
                if inputs and isinstance(inputs[0], str):
                    query = inputs[0]
                
                result = await notion_service.search(
                    api_key=api_key,
                    query=query
                )
                return result
            
            elif action == "update_block_children":
                block_id = api_config.get("blockId", "")
                children = api_config.get("children", [])
                after = api_config.get("after", None)
                
                # If inputs provided, use the first input as children
                if inputs and isinstance(inputs[0], (list, str)):
                    if isinstance(inputs[0], str):
                        # Try to parse as JSON
                        try:
                            children = json.loads(inputs[0])
                        except:
                            # If not JSON, create a simple paragraph block
                            children = [{
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "text": [{"type": "text", "text": {"content": inputs[0]}}]
                                }
                            }]
                    else:
                        children = inputs[0]
                
                result = await notion_service.update_block_children(
                    api_key=api_key,
                    block_id=block_id,
                    children=children,
                    after=after
                )
                return result
            
            else:
                raise ValueError(f"Unknown Notion action: {action}")

        elif api_type == "web_search":
            from ..services.web_search_service import WebSearchService
            search_service = WebSearchService()

            # Get search query from config or inputs
            query = api_config.get("query", "")
            if inputs and isinstance(inputs[0], str):
                query = inputs[0]

            if not query:
                raise ValueError("Search query is required")

            # Get API key - you'll need to handle this based on your API key management
            api_key_id = api_config.get("apiKeyId")
            if api_key_id:
                api_key_data = self.llm_service.api_key_service.get_api_key(api_key_id)
                api_key = api_key_data["key"]
            else:
                raise ValueError("API key is required for web search")

            # Perform search
            provider = api_config.get("provider", "serper")
            num_results = api_config.get("numResults", 10)

            results = await search_service.search(
                query=query,
                api_key=api_key,
                provider=provider,
                num_results=num_results
            )

            # Format results based on configuration
            format_type = api_config.get("outputFormat", "full")
            if format_type == "urls_only":
                return [r.get("link") for r in results.get("organic", [])]
            elif format_type == "snippets":
                return [{"title": r.get("title"), "snippet": r.get("snippet")}
                        for r in results.get("organic", [])]
            else:
                return results
        else:
            raise ValueError(f"Unknown API type: '{api_type}'. Available types: 'notion'")


class ExecutionScheduler:
    """Manages the execution queue and scheduling logic."""
    
    def __init__(self, dynamic_executor: DynamicExecutor, state: ExecutionState):
        self.dynamic_executor = dynamic_executor
        self.state = state
        self.requeue_count: Dict[str, int] = {}
        
    def should_skip_node(self, nid: str) -> Tuple[bool, Optional[str]]:
        """Check if node should be skipped due to max iterations."""
        if nid not in self.state.node_max_iterations:
            return False, None
            
        max_iter = self.state.node_max_iterations[nid]
        if self.state.counts[nid] >= max_iter:
            logger.debug(f"[Node {nid}] Skipping - exceeded max iterations ({max_iter})")
            return True, "max_iterations_exceeded"
            
        return False, None
    
    def check_dependencies(self, nid: str) -> Tuple[bool, List[dict]]:
        """Check if node dependencies are met."""
        deps_met, valid_incoming = self.dynamic_executor.check_dependencies_met(
            nid,
            set(self.state.context.keys()),
            self.state.condition_values,
            self.state.context
        )
        return deps_met, valid_incoming
    
    def handle_requeue(self, nid: str) -> bool:
        """Handle requeuing of nodes with unmet dependencies."""
        self.requeue_count[nid] = self.requeue_count.get(nid, 0) + 1
        logger.debug(f"[Node {nid}] Dependencies not met, re-queueing (attempt {self.requeue_count[nid]})")
        
        if self.requeue_count[nid] > 100:
            logger.debug(f"[ERROR] Node {nid} has been requeued too many times. Breaking infinite loop.")
            return False
            
        return True
    
    def get_next_nodes(self, nid: str) -> List[str]:
        """Get the next nodes to execute after current node."""
        return self.dynamic_executor.get_next_nodes(nid, self.state.condition_values)


class DiagramExecutor:
    """Executes a block‑diagram and returns (context, total_cost). Supports streaming node status updates via callback."""

    def __init__(self,
                 diagram: dict,
                 memory_service: MemoryService = None,
                 status_callback: Optional[Callable[[dict], Awaitable[None]]] = None):
        self.diagram = diagram
        self.nodes: List[dict] = diagram.get("nodes", [])
        self.arrows: List[dict] = diagram.get("arrows", [])
        persons_list = diagram.get("persons", [])
        self.persons: Dict[str, dict] = {p["id"]: p for p in persons_list}

        self.status_callback = status_callback

        api_key_service = APIKeyService()
        self.llm_service = LLMService(api_key_service)
        self.memory_service = memory_service or MemoryService()

        import uuid
        self.execution_id = str(uuid.uuid4())

        self.nodes_by_id: Dict[str, dict] = {n["id"]: n for n in self.nodes}
        self.node_types: Dict[str, str] = {nid: n["type"] for nid, n in self.nodes_by_id.items()}
        logger.debug(f"[Init] Node types: {self.node_types}")

        # Initialize execution state
        self.state = ExecutionState(
            context={},
            condition_values={},
            counts=Counter(),
            total_cost=0.0,
            node_max_iterations=self._extract_max_iterations()
        )
        
        # Initialize helper classes
        self.node_executor = NodeExecutor(
            nodes=self.nodes_by_id,
            persons=self.persons,
            llm_service=self.llm_service,
            memory_service=self.memory_service,
            execution_id=self.execution_id,
            send_status_update_fn=self._send_status_update
        )

    def _extract_max_iterations(self) -> Dict[str, int]:
        """Extract iterationCount for nodes that need it."""
        node_max_iterations = {}
        for node in self.nodes:
            data = node.get("data", {})
            if "iterationCount" in data and data["iterationCount"] is not None:
                try:
                    max_iter = int(data["iterationCount"])
                    if max_iter > 0:
                        node_max_iterations[node["id"]] = max_iter
                except (ValueError, TypeError):
                    pass
        return node_max_iterations

    async def _send_status_update(self, update_type: str, node_id: str, **extra_data):
        """Send status update via callback if available."""
        if self.status_callback:
            update = {
                "type": update_type,
                "nodeId": node_id,
                "timestamp": datetime.now().isoformat(),
                **extra_data
            }
            try:
                await self.status_callback(update)
            except Exception as e:
                logger.debug(f"Warning: Failed to send status update: {e}")

    async def run(self) -> Tuple[Dict[str, Any], float]:
        """Execute the diagram with dynamic execution order based on condition results."""
        dynamic_executor = DynamicExecutor(self.nodes, self.arrows)
        execution_plan = dynamic_executor.create_execution_plan()

        if execution_plan["has_cycles"]:
            logger.debug(f"[Warning] Cycles detected in diagram: {execution_plan['cycle_nodes']}")

        scheduler = ExecutionScheduler(dynamic_executor, self.state)
        execution_queue = deque(execution_plan["start_nodes"])
        executed_in_iteration = set()

        while execution_queue:
            nid = execution_queue.popleft()
            logger.debug(f"\n[Execution] Processing node: {nid}")
            
            # Skip if already executed in this iteration
            execution_key = f"{nid}_{self.state.counts[nid]}"
            if execution_key in executed_in_iteration:
                continue

            # Check if node should be skipped
            should_skip, skip_reason = scheduler.should_skip_node(nid)
            if should_skip:
                self.state.context[nid] = {"skipped_max_iter": True}
                await self._send_status_update("node_skipped", nid, reason=skip_reason)
                
                next_nodes = scheduler.get_next_nodes(nid)
                execution_queue.extend(n for n in next_nodes if n not in execution_queue)
                continue

            # Check dependencies
            deps_met, valid_incoming = scheduler.check_dependencies(nid)
            if not deps_met:
                if not scheduler.handle_requeue(nid):
                    break
                execution_queue.append(nid)
                continue

            # Skip nodes with no valid incoming arrows (except start nodes)
            node = self.nodes_by_id[nid]
            if node.get("type") not in ["startNode", "start"] and not valid_incoming:
                logger.debug(f"[Node {nid}] Skipping - no valid incoming arrows after branch filtering")
                continue

            # Execute the node
            await self._execute_node_with_tracking(nid, node, valid_incoming, executed_in_iteration)
            
            # Queue next nodes
            next_nodes = scheduler.get_next_nodes(nid)
            dynamic_executor.mark_first_only_consumed(nid)
            execution_queue.extend(n for n in next_nodes if n not in execution_queue)

            # Check for endpoint
            try:
                current_type = NodeType.from_legacy(node.get("type", ""))
                if current_type == NodeType.ENDPOINT:
                    logger.debug(f"[Execution] Reached endpoint node {nid}, stopping execution.")
                    break
            except Exception:
                pass

        # Log unexecuted nodes
        self._log_unexecuted_nodes(executed_in_iteration, dynamic_executor)
        
        return self.state.context, self.state.total_cost

    async def _execute_node_with_tracking(
            self, 
            nid: str, 
            node: dict, 
            valid_incoming: List[dict],
            executed_in_iteration: Set[str]
    ):
        """Execute a single node with status tracking."""
        logger.debug(f"[Node {nid}] Executing (iteration {self.state.counts[nid] + 1})")
        self.state.counts[nid] += 1
        execution_key = f"{nid}_{self.state.counts[nid] - 1}"
        executed_in_iteration.add(execution_key)

        await self._send_status_update("node_start", nid)
        
        # Add small delay to make visual feedback visible
        await asyncio.sleep(0.1)

        try:
            vars_map, inputs = resolve_inputs(nid, valid_incoming, self.state.context)
            output, cost = await self.node_executor.execute_node(
                node, vars_map, inputs, valid_incoming, self.state
            )
            
            self.state.context[nid] = output
            self.state.total_cost += cost

            # Handle output preview for different output types
            if isinstance(output, dict) and output.get('_type') == 'personjob_output':
                preview = str(output.get('text', ''))[:100]
            else:
                preview = str(output)[:100] if output else None
            
            await self._send_status_update(
                "node_complete", 
                nid,
                output_preview=preview
            )

        except Exception as e:
            await self._send_status_update("node_error", nid, error=str(e))
            raise

    def _log_unexecuted_nodes(self, executed_in_iteration: Set[str], dynamic_executor: DynamicExecutor):
        """Log any nodes that were not executed."""
        executed_node_ids = {key.split('_')[0] for key in executed_in_iteration}
        unexecuted = set(self.nodes_by_id.keys()) - executed_node_ids

        if unexecuted:
            legitimate_skips = set()
            for nid in unexecuted:
                deps_met, _ = dynamic_executor.check_dependencies_met(
                    nid,
                    set(self.state.context.keys()),
                    self.state.condition_values,
                    self.state.context
                )
                if not deps_met:
                    legitimate_skips.add(nid)

            actually_unexecuted = unexecuted - legitimate_skips
            if actually_unexecuted:
                logger.debug(f"[Warning] Nodes not executed (and not on skipped branches): {actually_unexecuted}")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics from the memory service."""
        return self.memory_service.get_memory_stats()