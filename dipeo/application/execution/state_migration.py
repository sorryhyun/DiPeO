"""State migration system for handling format upgrades."""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class StateVersion(str, Enum):
    """State format versions."""
    V1 = "1.0"  # Initial version
    V2 = "2.0"  # Typed outputs, separated history
    V3 = "3.0"  # Future: event-sourced format
    
    @classmethod
    def get_latest(cls) -> "StateVersion":
        """Get the latest version."""
        return cls.V2


@dataclass
class MigrationResult:
    """Result of a state migration."""
    success: bool
    data: Dict[str, Any]
    version: StateVersion
    errors: list[str]


class StateMigrator:
    """Handles state format migrations between versions."""
    
    def __init__(self):
        self._migrations: Dict[tuple[StateVersion, StateVersion], Callable] = {
            (StateVersion.V1, StateVersion.V2): self._migrate_v1_to_v2,
        }
    
    def migrate(self, state_data: Dict[str, Any], target_version: Optional[StateVersion] = None) -> MigrationResult:
        """Migrate state data to target version."""
        target_version = target_version or StateVersion.get_latest()
        current_version = self._detect_version(state_data)
        
        if current_version == target_version:
            return MigrationResult(
                success=True,
                data=state_data,
                version=current_version,
                errors=[]
            )
        
        # Build migration path
        path = self._find_migration_path(current_version, target_version)
        if not path:
            return MigrationResult(
                success=False,
                data=state_data,
                version=current_version,
                errors=[f"No migration path from {current_version} to {target_version}"]
            )
        
        # Apply migrations
        result_data = state_data.copy()
        errors = []
        
        for from_ver, to_ver in path:
            migration_fn = self._migrations.get((from_ver, to_ver))
            if not migration_fn:
                errors.append(f"Missing migration function from {from_ver} to {to_ver}")
                break
                
            try:
                result_data = migration_fn(result_data)
                result_data["_version"] = to_ver.value
            except Exception as e:
                errors.append(f"Migration from {from_ver} to {to_ver} failed: {str(e)}")
                break
        
        return MigrationResult(
            success=len(errors) == 0,
            data=result_data,
            version=self._detect_version(result_data),
            errors=errors
        )
    
    def _detect_version(self, state_data: Dict[str, Any]) -> StateVersion:
        """Detect state format version."""
        # Check explicit version marker
        if "_version" in state_data:
            try:
                return StateVersion(state_data["_version"])
            except ValueError:
                logger.warning(f"Unknown version: {state_data['_version']}, falling back to V1")
        
        # Detect V2 features
        if "node_outputs" in state_data:
            for output in state_data.get("node_outputs", {}).values():
                if isinstance(output, dict) and "value" in output:
                    return StateVersion.V2
                if isinstance(output, dict) and "output_type" in output:
                    return StateVersion.V2
        
        # Default to V1
        return StateVersion.V1
    
    def _find_migration_path(self, from_version: StateVersion, to_version: StateVersion) -> list[tuple[StateVersion, StateVersion]]:
        """Find migration path between versions."""
        # Simple linear path for now
        versions = list(StateVersion)
        from_idx = versions.index(from_version)
        to_idx = versions.index(to_version)
        
        if from_idx >= to_idx:
            return []
        
        path = []
        for i in range(from_idx, to_idx):
            path.append((versions[i], versions[i + 1]))
        
        return path
    
    def _migrate_v1_to_v2(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from V1 to V2 format."""
        result = state_data.copy()
        
        # Convert node_outputs to typed format
        if "node_outputs" in result:
            new_outputs = {}
            for node_id, output_data in result["node_outputs"].items():
                if isinstance(output_data, dict) and "value" in output_data:
                    # Already has the correct NodeOutput format
                    new_outputs[node_id] = output_data
                elif isinstance(output_data, dict) and "output_type" in output_data:
                    # Convert from incorrect V2 format to NodeOutput format
                    new_outputs[node_id] = {
                        "value": output_data.get("data", {}),
                        "metadata": output_data.get("metadata", {}),
                        "node_id": node_id,
                        "executed_nodes": output_data.get("executed_nodes", None)
                    }
                else:
                    # Convert from V1 format
                    new_outputs[node_id] = {
                        "value": output_data if output_data is not None else {},
                        "metadata": {},
                        "node_id": node_id,
                        "executed_nodes": None
                    }
            result["node_outputs"] = new_outputs
        
        # Ensure exec_counts exists
        if "exec_counts" not in result:
            result["exec_counts"] = {}
        
        # Ensure executed_nodes exists
        if "executed_nodes" not in result:
            result["executed_nodes"] = []
        
        return result


def add_version_to_state(state_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add version marker to state dictionary."""
    if "_version" not in state_dict:
        state_dict["_version"] = StateVersion.get_latest().value
    return state_dict


def remove_version_from_state(state_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Remove version marker from state dictionary (for backward compatibility)."""
    result = state_dict.copy()
    result.pop("_version", None)
    return result