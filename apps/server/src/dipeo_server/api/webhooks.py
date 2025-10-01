"""Webhook gateway for receiving and processing provider webhooks."""

import hashlib
import hmac
import json
import time
from typing import Any

from dipeo.config.base_logger import get_module_logger
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from dipeo.domain.events import (
    DomainEvent,
    EventScope,
    EventType,
    ExecutionLogPayload,
)
from dipeo.infrastructure.events.adapters import InMemoryEventBus
from dipeo.infrastructure.integrations.drivers.integrated_api.registry import (
    ProviderRegistry,
)

logger = get_module_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def create_webhook_event(
    provider: str,
    event_name: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    execution_id: str | None = None,
) -> DomainEvent:
    """Create a webhook received domain event."""
    exec_id = execution_id or f"webhook-{provider}-{int(time.time())}"

    return DomainEvent(
        type=EventType.EXECUTION_LOG,
        scope=EventScope(execution_id=exec_id),
        payload=ExecutionLogPayload(
            level="INFO",
            message=f"Webhook received from {provider}: {event_name}",
            logger_name="webhook_processor",
            extra_fields={
                "webhook_id": f"{provider}-{event_name}-{int(time.time())}",
                "source": provider,
                "event_name": event_name,
                "payload": payload,
                "headers": headers,
            },
        ),
    )


class WebhookProcessor:
    """Process and validate incoming webhooks."""

    def __init__(self, registry: ProviderRegistry, event_bus: InMemoryEventBus):
        self.registry = registry
        self.event_bus = event_bus

    async def validate_webhook_signature(
        self, provider_name: str, headers: dict[str, str], body: bytes
    ) -> bool:
        """Validate webhook signature based on provider configuration.

        Different providers use different signature validation methods:
        - Slack: HMAC-SHA256 with 'X-Slack-Signature' header
        - GitHub: HMAC-SHA256 with 'X-Hub-Signature-256' header
        - Stripe: HMAC-SHA256 with 'Stripe-Signature' header
        """
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return False

        # Get provider manifest if available
        manifest = getattr(provider, "manifest", None)
        if not manifest:
            # Provider doesn't have webhook configuration
            return True  # Allow unsigned webhooks for providers without config

        # Check if provider has webhook signature configuration
        webhook_config = manifest.metadata.get("webhook_config", {}) if manifest.metadata else {}
        if not webhook_config:
            return True  # No signature validation required

        signature_header = webhook_config.get("signature_header")
        signature_algorithm = webhook_config.get("signature_algorithm", "hmac_sha256")
        secret_key = webhook_config.get("secret")  # This should come from secure storage

        if not signature_header or not secret_key:
            logger.warning(f"Webhook signature validation not configured for {provider_name}")
            return True

        received_signature = headers.get(signature_header.lower())
        if not received_signature:
            logger.warning(f"Missing signature header {signature_header} for {provider_name}")
            return False

        # Validate based on algorithm
        if signature_algorithm == "hmac_sha256":
            expected = hmac.new(secret_key.encode(), body, hashlib.sha256).hexdigest()

            # Some providers prefix the signature
            if "=" in received_signature:
                received_signature = received_signature.split("=")[-1]

            return hmac.compare_digest(expected, received_signature)

        logger.warning(f"Unsupported signature algorithm: {signature_algorithm}")
        return False

    async def normalize_webhook_payload(
        self, provider_name: str, raw_payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Normalize webhook payload to a standard format.

        Each provider has different payload structures. This method
        normalizes them to a common format for easier processing.
        """
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return raw_payload

        # Get normalization rules from provider manifest
        manifest = getattr(provider, "manifest", None)
        if not manifest or not manifest.webhook_events:
            return raw_payload

        # Basic normalization - extract common fields
        normalized = {
            "provider": provider_name,
            "timestamp": time.time(),
            "raw_payload": raw_payload,
        }

        # Provider-specific normalization
        if provider_name == "slack":
            normalized.update(
                {
                    "event_type": raw_payload.get("type", "unknown"),
                    "team_id": raw_payload.get("team_id"),
                    "event_id": raw_payload.get("event_id"),
                    "event_data": raw_payload.get("event", {}),
                }
            )
        elif provider_name == "github":
            normalized.update(
                {
                    "event_type": raw_payload.get("action", "unknown"),
                    "repository": raw_payload.get("repository", {}).get("full_name"),
                    "sender": raw_payload.get("sender", {}).get("login"),
                    "event_data": raw_payload,
                }
            )
        else:
            # Generic normalization
            normalized.update(
                {
                    "event_type": raw_payload.get("event") or raw_payload.get("type") or "unknown",
                    "event_data": raw_payload,
                }
            )

        return normalized

    async def process_webhook(
        self, provider_name: str, headers: dict[str, str], body: bytes
    ) -> dict[str, Any]:
        """Process an incoming webhook."""
        # Validate signature
        if not await self.validate_webhook_signature(provider_name, headers, body):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        # Parse payload
        try:
            raw_payload = json.loads(body)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {e}",
            )

        # Normalize payload
        normalized_payload = await self.normalize_webhook_payload(provider_name, raw_payload)

        # Determine event name from headers or payload
        event_name = self._extract_event_name(provider_name, headers, raw_payload)

        # Create webhook event
        webhook_event = create_webhook_event(
            provider=provider_name,
            event_name=event_name,
            payload=normalized_payload,
            headers=dict(headers),
        )

        # Emit event to event bus
        await self.event_bus.publish(webhook_event)

        return {
            "status": "processed",
            "provider": provider_name,
            "event": event_name,
            "execution_id": webhook_event.scope.execution_id,
        }

    def _extract_event_name(
        self, provider_name: str, headers: dict[str, str], payload: dict[str, Any]
    ) -> str:
        """Extract event name from headers or payload based on provider."""
        # Provider-specific event extraction
        if provider_name == "github":
            return headers.get("x-github-event", "unknown")
        if provider_name == "slack":
            return payload.get("type") or payload.get("event", {}).get("type", "unknown")
        if provider_name == "stripe":
            return payload.get("type", "unknown")

        # Generic extraction
        return (
            headers.get("x-event-type")
            or headers.get("x-webhook-event")
            or payload.get("event")
            or payload.get("type")
            or "unknown"
        )


@router.post("/{provider}")
async def receive_webhook(provider: str, request: Request, response: Response) -> JSONResponse:
    """Receive and process a webhook from a provider.

    This endpoint:
    1. Validates the webhook signature (if configured)
    2. Normalizes the payload to a standard format
    3. Emits an event to the execution event bus
    4. Returns a success response to the provider
    """
    try:
        # Get container from app context
        from dipeo.application.registry.keys import EVENT_BUS, PROVIDER_REGISTRY
        from dipeo_server.app_context import get_container

        container = get_container()
        registry = container.registry.resolve(PROVIDER_REGISTRY)
        event_bus = container.registry.resolve(EVENT_BUS)

        if not registry:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Provider registry not available",
            )

        if not event_bus:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Event bus not available",
            )

        # Check if provider exists
        if not registry.get_provider(provider):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider}' not found",
            )

        # Get request body and headers
        body = await request.body()
        headers = dict(request.headers)

        # Process webhook
        processor = WebhookProcessor(registry, event_bus)
        result = await processor.process_webhook(provider, headers, body)

        # Some providers expect specific response codes
        if provider == "slack":
            # Slack expects a 200 OK with no body for URL verification
            if json.loads(body).get("type") == "url_verification":
                challenge = json.loads(body).get("challenge")
                return JSONResponse(content={"challenge": challenge})

        response.status_code = status.HTTP_200_OK
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook from {provider}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {e!s}",
        )


@router.get("/{provider}/test")
async def test_webhook_endpoint(provider: str) -> dict[str, Any]:
    """Test endpoint to verify webhook configuration.

    Returns information about the webhook configuration for a provider.
    """
    try:
        # This would get the container from app context
        from dipeo_server.app_context import get_container

        container = get_container()
        registry = container.registry.get("provider_registry")

        if not registry:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Provider registry not available",
            )

        provider_instance = registry.get_provider(provider)
        if not provider_instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider}' not found",
            )

        # Get webhook configuration from manifest
        manifest = getattr(provider_instance, "manifest", None)
        if not manifest:
            return {
                "provider": provider,
                "webhook_support": False,
                "message": "Provider does not have webhook configuration",
            }

        webhook_events = manifest.webhook_events or []
        webhook_config = manifest.metadata.get("webhook_config", {}) if manifest.metadata else {}

        return {
            "provider": provider,
            "webhook_support": bool(webhook_events),
            "webhook_url": f"/webhooks/{provider}",
            "supported_events": [
                {
                    "name": event.name,
                    "description": event.description,
                    "has_schema": bool(event.payload_schema),
                }
                for event in webhook_events
            ],
            "signature_validation": bool(webhook_config.get("signature_header")),
            "signature_header": webhook_config.get("signature_header"),
            "test_mode": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook info for {provider}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook information: {e!s}",
        )
