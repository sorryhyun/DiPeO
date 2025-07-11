# Centralized handler for on_every_turn forgetting mode logic

from typing import Any, Dict, List, Optional, Tuple


class OnEveryTurnHandler:
    # Handles the on_every_turn forgetting mode logic in a centralized way
    
    @staticmethod
    def filter_messages_for_output(
        messages: List[Dict[str, Any]], 
        person_id: str,
        execution_id: str
    ) -> List[Dict[str, Any]]:
        # Returns only the last assistant message from each other person
        last_messages_by_person = {}
        
        for msg in messages:
            if msg.get("execution_id") != execution_id:
                continue
                
            # Check if this message is FROM another person TO this person
            from_person = msg.get("from_person_id")
            to_person = msg.get("to_person_id")
            
            # We want messages where someone else sent TO this person
            if (to_person == person_id and 
                from_person != person_id and 
                from_person != "system" and
                msg.get("role") == "assistant"):
                # Keep only the latest message from each person
                last_messages_by_person[from_person] = {
                    "role": msg.get("role"),
                    "content": msg.get("content", ""),
                    "from_person_id": from_person
                }
        
        return list(last_messages_by_person.values())
    
    @staticmethod
    def consolidate_conversation_inputs(
        inputs: Dict[str, Any],
        used_template_keys: set,
        diagram: Optional[Any] = None
    ) -> Tuple[str, List[str]]:
        # Extracts and formats last assistant message from each person with labels
        person_messages = {}
        person_labels = []
        
        for key, value in inputs.items():
            if key in used_template_keys:
                continue
                
            if isinstance(value, list) and value:
                # Check if this is conversation data
                for msg in value:
                    if (isinstance(msg, dict) and 
                        msg.get("role") == "assistant" and 
                        msg.get("person_id")):
                        person_id = msg.get("person_id")
                        sender_label = msg.get("person_label", person_id)
                        
                        # Use person label from diagram if available
                        if diagram:
                            person = next((p for p in diagram.persons if p.id == person_id), None)
                            if person and person.label:
                                sender_label = person.label
                        
                        person_messages[person_id] = f"[{sender_label}]: {msg.get('content', '')}"
                        if sender_label not in person_labels:
                            person_labels.append(sender_label)
        
        # Combine all messages
        consolidated_content = "\n\n".join(person_messages.values())
        return consolidated_content, person_labels
    
    @staticmethod
    def should_forget_messages(
        execution_count: int,
        forget_mode: Optional[str]
    ) -> bool:
        # Determine if messages should be forgotten based on mode and execution count
        return (forget_mode == "on_every_turn" and 
                execution_count > 0)
    
    @staticmethod
    def filter_rebuild_messages(
        messages: List[Dict[str, Any]],
        person_id: str,
        forget_mode: Optional[str]
    ) -> List[Dict[str, Any]]:
        # For on_every_turn mode, filters out messages from the receiving person itself
        if forget_mode != "on_every_turn":
            return messages
            
        # Filter out messages from the person itself
        return [
            msg for msg in messages 
            if msg.get("from_person_id") != person_id
        ]