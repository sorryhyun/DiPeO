# Implementation of ConversationManager protocol using Person and PersonManager.

import json
from datetime import datetime
from typing import Any, Optional

from pathlib import Path
from dipeo.core import BaseService
from dipeo.core.dynamic.conversation import Conversation
from dipeo.core.dynamic.conversation_manager import ConversationManager
from dipeo.core.dynamic.person import Person
from dipeo.core.dynamic.person_manager import PersonManager
from dipeo.core.utils import is_conversation
from dipeo.models import (
    ApiKeyID,
    ForgettingMode,
    LLMService,
    Message,
    PersonID,
    PersonLLMConfig,
)
from dipeo.utils.conversation import OnEveryTurnHandler


class PersonManagerImpl(PersonManager):
    
    def __init__(self, conversation_manager: Optional[ConversationManager] = None):
        self._persons: dict[PersonID, Person] = {}
        self._conversation_manager = conversation_manager
    
    def get_person(self, person_id: PersonID) -> Person:
        if person_id not in self._persons:
            raise KeyError(f"Person {person_id} not found")
        return self._persons[person_id]
    
    def create_person(
        self,
        person_id: PersonID,
        name: str,
        llm_config: PersonLLMConfig,
        role: str | None = None
    ) -> Person:
        person = Person(
            id=person_id, 
            name=name, 
            llm_config=llm_config,
            conversation_manager=self._conversation_manager
        )
        self._persons[person_id] = person
        return person
    
    def update_person_config(
        self,
        person_id: PersonID,
        llm_config: PersonLLMConfig | None = None,
        role: str | None = None
    ) -> None:
        person = self.get_person(person_id)
        if llm_config:
            person.llm_config = llm_config
    
    def get_all_persons(self) -> dict[PersonID, Person]:
        return self._persons.copy()
    
    def get_persons_by_service(self, service: LLMService) -> list[Person]:
        return [
            person for person in self._persons.values()
            if person.llm_config.service == service
        ]
    
    def remove_person(self, person_id: PersonID) -> None:
        if person_id in self._persons:
            del self._persons[person_id]
    
    def clear_all_persons(self) -> None:
        self._persons.clear()
    
    def person_exists(self, person_id: PersonID) -> bool:
        return person_id in self._persons


class ConversationManagerImpl(BaseService, ConversationManager):
    # Maintains a single global conversation that all persons share
    
    def __init__(self):
        super().__init__()
        self.person_manager = PersonManagerImpl(conversation_manager=self)
        self._current_execution_id: str | None = None
        self._conversation_logs: dict[str, list[dict[str, Any]]] = {}
        # Single global conversation shared by all persons
        self._global_conversation = Conversation()
    
    def get_conversation(self, person_id: str) -> Conversation:
        return self._global_conversation
    
    def create_conversation(self, person_id: str) -> Conversation:
        person_id_obj = PersonID(person_id)
        
        if self.person_manager.person_exists(person_id_obj):
            person = self.person_manager.get_person(person_id_obj)
            person.clear_conversation()
        
        return self._global_conversation
    
    def get_or_create_conversation(self, person_id: str) -> Conversation:
        person_id_obj = PersonID(person_id)
        if self.person_manager.person_exists(person_id_obj):
            return self.get_conversation(person_id)
        else:
            return self.create_conversation(person_id)
    
    def add_message(
        self,
        message: Message,
        execution_id: str,
        node_id: str | None = None
    ) -> None:
        self._current_execution_id = execution_id
        
        if message.from_person_id != "system":
            self._add_to_person_conversation(
                str(message.from_person_id), 
                message, 
                execution_id, 
                node_id
            )
        
        if message.to_person_id != "system" and message.to_person_id != message.from_person_id:
            self._add_to_person_conversation(
                str(message.to_person_id), 
                message, 
                execution_id, 
                node_id
            )
        
        if message.from_person_id == message.to_person_id and message.from_person_id != "system":
            pass
    
    def _add_to_person_conversation(
        self,
        person_id: str,
        message: Message,
        execution_id: str,
        node_id: str | None = None
    ) -> None:
        person_id_obj = PersonID(person_id)
        person = self.person_manager.get_person(person_id_obj) if self.person_manager.person_exists(person_id_obj) else None
        
        if not person:
            return
        
        person.add_message(message)
        
        if execution_id not in self._conversation_logs:
            self._conversation_logs[execution_id] = []
        self._conversation_logs[execution_id].append({
            "person_id": person_id,
            "role": self._get_role_from_message(message),
            "content": message.content,
            "from_person_id": str(message.from_person_id),
            "to_person_id": str(message.to_person_id),
            "node_id": node_id,
            "timestamp": message.timestamp
        })
    
    def apply_forgetting(
        self,
        person_id: str,
        mode: ForgettingMode,
        execution_id: str | None = None
    ) -> int:
        execution_id = execution_id or self._current_execution_id
        
        if mode == ForgettingMode.on_every_turn:
            person_id_obj = PersonID(person_id)
            if not self.person_manager.person_exists(person_id_obj):
                return 0
            
            person = self.person_manager.get_person(person_id_obj)
            original_count = person.get_message_count()
            
            messages = person.get_messages()
            person.clear_conversation()
            
            for msg in messages:
                if msg.from_person_id != person_id:
                    person.add_message(msg)
            
            if execution_id and execution_id in self._conversation_logs:
                self._conversation_logs[execution_id] = [
                    log for log in self._conversation_logs[execution_id]
                    if not (log["person_id"] == person_id and log["from_person_id"] == person_id)
                ]
            
            return original_count - person.get_message_count()
        
        elif mode == ForgettingMode.upon_request:
            person_id_obj = PersonID(person_id)
            if not self.person_manager.person_exists(person_id_obj):
                return 0
            
            person = self.person_manager.get_person(person_id_obj)
            count = person.get_message_count()
            person.clear_conversation()
            
            if execution_id and execution_id in self._conversation_logs:
                self._conversation_logs[execution_id] = [
                    log for log in self._conversation_logs[execution_id]
                    if log["person_id"] != person_id
                ]
            
            return count
        
        return 0
    
    def merge_conversations(
        self,
        source_person_id: str,
        target_person_id: str
    ) -> None:
        source_person = self.person_manager.get_person(PersonID(source_person_id))
        target_person = self.person_manager.get_person(PersonID(target_person_id))
        
        for message in source_person.get_messages():
            target_person.add_message(message)
        
        source_person.clear_conversation()
    
    def clear_conversation(
        self,
        person_id: str,
        execution_id: str | None = None
    ) -> None:
        execution_id = execution_id or self._current_execution_id
        
        person_id_obj = PersonID(person_id)
        if self.person_manager.person_exists(person_id_obj):
            person = self.person_manager.get_person(person_id_obj)
            person.clear_conversation()
        
        if execution_id and execution_id in self._conversation_logs:
            self._conversation_logs[execution_id] = [
                log for log in self._conversation_logs[execution_id]
                if log["person_id"] != person_id
            ]
    
    def get_all_conversations(self) -> dict[str, Conversation]:
        conversations = {}
        for person_id in self.person_manager.get_all_persons().keys():
            conversations[str(person_id)] = self._global_conversation
        return conversations
    
    
    def _load_existing_messages(self, person_id: str) -> None:
        person_id_obj = PersonID(person_id)
        person = self.person_manager.get_person(person_id_obj)
        
        if not self._current_execution_id or self._current_execution_id not in self._conversation_logs:
            return
            
        history = [
            log for log in self._conversation_logs[self._current_execution_id]
            if log["person_id"] == person_id
        ]
        
        if history is None:
            return
        
        for msg_dict in history:
            message = self._dict_to_message(msg_dict, person_id)
            if message:
                person.add_message(message)
    
    def _dict_to_message(self, msg_dict: dict[str, Any], person_id: str) -> Message | None:
        if self._current_execution_id and msg_dict.get("execution_id") != self._current_execution_id:
            return None
        
        from_person_id = msg_dict.get("from_person_id", msg_dict.get("current_person_id", person_id))
        to_person_id = msg_dict.get("to_person_id", person_id)
        
        role = msg_dict.get("role", "user")
        if role == "system":
            from_person_id = "system"
            message_type = "system_to_person"
        elif role == "external":
            message_type = "person_to_person"
        else:
            message_type = "person_to_person"
        
        return Message(
            from_person_id=PersonID(from_person_id) if from_person_id != "system" else "system",  # type: ignore
            to_person_id=PersonID(to_person_id) if to_person_id != "system" else "system",  # type: ignore
            content=msg_dict.get("content", ""),
            timestamp=msg_dict.get("timestamp"),
            message_type=message_type,  # type: ignore
            metadata={"role": role, "node_id": msg_dict.get("node_id")}
        )
    
    @staticmethod
    def _get_role_from_message(message: Message) -> str:
        if message.from_person_id == "system":
            return "system"
        elif message.from_person_id == message.to_person_id:
            return "assistant"
        else:
            return "user"
    
    def set_execution_id(self, execution_id: str) -> None:
        self._current_execution_id = execution_id
    
    
    async def initialize(self) -> None:
        pass
    
    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        
        person_id_obj = PersonID(person_id)
        if not self.person_manager.person_exists(person_id_obj):
            llm_config = PersonLLMConfig(
                service=LLMService(config.get('service', 'openai')),
                model=config.get('model', 'gpt-4'),
                api_key_id=ApiKeyID(config.get('api_key_id', 'default')),
                system_prompt=config.get('system_prompt'),
                temperature=config.get('temperature'),
                max_tokens=config.get('max_tokens')
            )
            person = Person(
                id=person_id_obj,
                name=config.get('name', person_id),
                llm_config=llm_config,
                conversation_manager=self
            )
            self.person_manager._persons[person_id_obj] = person
    
    def get_person_config(self, person_id: str) -> dict[str, Any] | None:
        person_id_obj = PersonID(person_id)
        if self.person_manager.person_exists(person_id_obj):
            person = self.person_manager.get_person(person_id_obj)
            if person.llm_config:
                return {
                    'service': person.llm_config.service.value,
                    'model': person.llm_config.model,
                    'api_key_id': str(person.llm_config.api_key_id),
                    'system_prompt': person.llm_config.system_prompt,
                    'temperature': person.llm_config.temperature,
                    'max_tokens': person.llm_config.max_tokens
                }
        return None
    
    def get_or_create_person_memory(self, person_id: str) -> Any:
        # TODO: deprecated - use get_or_create_conversation instead
        return self.get_or_create_conversation(person_id)
    
    def add_message_to_conversation(
        self,
        person_id: str,
        execution_id: str,
        role: str,
        content: str,
        current_person_id: str,
        node_id: str | None = None,
        timestamp: float | None = None,
    ) -> None:
        if execution_id:
            self._current_execution_id = execution_id
        
        if role == "system":
            from_person_id = "system"
            to_person_id = PersonID(person_id)
            message_type = "system_to_person"
        elif role == "assistant":
            from_person_id = PersonID(person_id)
            to_person_id = PersonID(current_person_id) if current_person_id != person_id else "system"
            message_type = "person_to_person" if current_person_id != person_id else "person_to_system"
        else:  # user or external
            from_person_id = PersonID(current_person_id) if current_person_id != person_id else "system"
            to_person_id = PersonID(person_id)
            message_type = "person_to_person" if current_person_id != person_id else "system_to_person"
        
        message = Message(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            content=content,
            message_type=message_type,  # type: ignore
            timestamp=timestamp,
            metadata={"role": role, "node_id": node_id}
        )
        
        self.add_message(
            message=message,
            execution_id=execution_id,
            node_id=node_id
        )
    
    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        conversation = self.get_conversation(person_id)
        history = []
        
        for msg in conversation.messages:
            history.append({
                "role": "assistant" if msg.from_person_id == person_id else "user",
                "content": msg.content,
                "from_person_id": str(msg.from_person_id),
                "to_person_id": str(msg.to_person_id),
                "execution_id": self._current_execution_id,
                "timestamp": msg.timestamp,
                "node_id": msg.metadata.get("node_id") if msg.metadata else None
            })
        
        return history
    
    def forget_for_person(
        self, person_id: str, execution_id: str | None = None
    ) -> None:
        execution_id = execution_id or self._current_execution_id
        self.clear_conversation(person_id, execution_id)
    
    def forget_own_messages_for_person(
        self, person_id: str, execution_id: str | None = None
    ) -> None:
        execution_id = execution_id or self._current_execution_id
        self.apply_forgetting(
            person_id,
            ForgettingMode.on_every_turn,
            execution_id
        )
    
    def clear_all_conversations(self) -> None:
        self._global_conversation.clear()
        
        for person_id in list(self.person_manager.get_all_persons().keys()):
            self.person_manager.remove_person(person_id)
        
        self._conversation_logs.clear()
    
    async def save_conversation_log(self, execution_id: str, log_dir: Path) -> str:
        import json
        from datetime import datetime
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"conversation_{execution_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = log_dir / filename
        
        conversations = {}
        for person_id, person in self.person_manager.get_all_persons().items():
            messages = []
            for msg in person.get_messages():
                messages.append({
                    "role": self._get_role_from_message(msg),
                    "content": msg.content,
                    "from_person_id": str(msg.from_person_id),
                    "to_person_id": str(msg.to_person_id),
                    "timestamp": msg.timestamp
                })
            conversations[str(person_id)] = messages
        
        with open(filepath, 'w') as f:
            json.dump({
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
                "conversations": conversations
            }, f, indent=2)
        
        return str(filepath)
    
    @staticmethod
    def is_conversation(value: Any) -> bool:
        return is_conversation(value)
    
    def add_simple_message(self, person_id: str, role: str, content: str) -> None:
        self.add_message_to_conversation(
            person_id=person_id,
            execution_id=self._current_execution_id or "",
            role=role,
            content=content,
            current_person_id=person_id
        )
    
    def get_messages(self, person_id: str) -> list[dict[str, str]]:
        if self._current_execution_id:
            conversation = self.get_conversation(person_id)
            messages = []
            
            for msg in conversation.messages:
                if str(msg.from_person_id) == person_id:
                    role = "assistant"
                elif msg.from_person_id == "system":
                    role = "system"
                else:
                    role = "user"
                
                messages.append({
                    "role": role,
                    "content": msg.content
                })
            
            return messages
        else:
            messages = []
            return messages
    
    def clear_messages(
        self, 
        person_id: str, 
        keep_system: bool = True,
        keep_user: bool = True,
        keep_assistant: bool = True,
        keep_external: bool = True
    ) -> None:
        if not keep_system and not keep_user and not keep_assistant and not keep_external:
            self.clear_conversation(person_id, self._current_execution_id)
        elif not keep_assistant:
            self.apply_forgetting(
                person_id, 
                ForgettingMode.on_every_turn,
                self._current_execution_id
            )
    
    def get_messages_for_output(self, person_id: str, forget_mode: str | None = None) -> list[dict[str, str]]:
        if forget_mode == "on_every_turn":
            if self._current_execution_id:
                conversation = self.get_conversation(person_id)
                
                filtered_messages = []
                for msg in conversation.messages:
                    if str(msg.from_person_id) != person_id:
                        role = "user" if msg.from_person_id != "system" else "system"
                        filtered_messages.append({
                            "role": role,
                            "content": msg.content
                        })
                
                return filtered_messages
            else:
                return []
        
        return self.get_messages(person_id)
    
    def prepare_messages_for_llm(self, person_id: str, system_prompt: str | None = None) -> list[dict[str, str]]:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        for msg in self.get_messages(person_id):
            role = "system" if msg["role"] == "external" else msg["role"]
            messages.append({"role": role, "content": msg["content"]})
        
        return messages
    
    def get_messages_with_person_id(self, person_id: str, forget_mode: str | None = None) -> list[dict[str, Any]]:
        messages = self.get_messages_for_output(person_id, forget_mode)
        
        messages_with_id = []
        for msg in messages:
            msg_with_person = msg.copy()
            msg_with_person["person_id"] = person_id
            messages_with_id.append(msg_with_person)
        
        return messages_with_id
    
    def rebuild_conversation_context(
        self, 
        person_id: str, 
        conversation_messages: list[dict[str, Any]], 
        clear_existing: bool = True,
        forget_mode: str | None = None
    ) -> None:
        if not isinstance(conversation_messages, list):
            return
        
        if clear_existing:
            self.forget_for_person(person_id, self._current_execution_id)
        
        conversation_messages = OnEveryTurnHandler.filter_rebuild_messages(
            conversation_messages, person_id, forget_mode
        )
        
        for msg in conversation_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "assistant" and msg.get("person_id") and msg.get("person_id") != person_id:
                sender_id = msg.get("person_id")
                sender_label = msg.get("person_label", sender_id)
                content = f"[{sender_label}]: {content}"
                role = "user"
            
            self.add_message_to_conversation(
                person_id=person_id,
                execution_id=self._current_execution_id or "",
                role=role,
                content=content,
                current_person_id=person_id
            )