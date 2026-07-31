from datetime import UTC, datetime, timedelta

import pytest

from app.database.db import Database
from app.database.repositories import (
    ActionExpiredError,
    ActionStateError,
    PendingActionRepository,
)
from app.services.software_catalog import SoftwareCatalog
from app.services.software_service import registry_from_catalog


def repository(tmp_path) -> PendingActionRepository:
    database = Database(tmp_path / "actions.db")
    database.initialize()
    return PendingActionRepository(database)


def test_pending_action_expires_after_ttl(tmp_path) -> None:
    repo = repository(tmp_path)
    definition = registry_from_catalog(SoftwareCatalog()).software_install("firefox")
    created = datetime(2026, 1, 1, tzinfo=UTC)
    action = repo.create(
        software_id="firefox",
        definition=definition,
        warning="Confirm install.",
        ttl=timedelta(minutes=5),
        now=created,
    )

    with pytest.raises(ActionExpiredError):
        repo.claim_for_confirmation(
            action.id, now=created + timedelta(minutes=5, seconds=1)
        )

    assert repo.get(action.id).state == "expired"


def test_cancelled_action_cannot_be_confirmed(tmp_path) -> None:
    repo = repository(tmp_path)
    definition = registry_from_catalog(SoftwareCatalog()).software_install("firefox")
    action = repo.create(
        software_id="firefox",
        definition=definition,
        warning="Confirm install.",
    )

    cancelled = repo.cancel(action.id)

    assert cancelled.state == "cancelled"
    with pytest.raises(ActionStateError):
        repo.claim_for_confirmation(action.id)


def test_executing_action_transitions_through_cancelling(tmp_path) -> None:
    repo = repository(tmp_path)
    definition = registry_from_catalog(SoftwareCatalog()).software_install("firefox")
    action = repo.create(
        software_id="firefox",
        definition=definition,
        warning="Confirm install.",
    )
    repo.claim_for_confirmation(action.id)

    cancelling = repo.request_execution_cancel(action.id)
    cancelled = repo.finish_execution_cancel(action.id)

    assert cancelling.state == "cancelling"
    assert cancelling.stage == "cancelling"
    assert cancelled.state == "cancelled"
    assert "quét lại" in cancelled.status_message
