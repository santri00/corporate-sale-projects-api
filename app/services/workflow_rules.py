"""Workflow state machine + automation rules.

Transition table (anything else -> 409):

    NEW               -> QUOTE_REQUESTED, HOLD, CANCELLED
    QUOTE_REQUESTED   -> PRODUCT_FINALIZED, HOLD, CANCELLED
    PRODUCT_FINALIZED -> COMPLETE, HOLD, CANCELLED
    HOLD              -> (resume) the state it was held from; or CANCELLED
    COMPLETE          -> terminal
    CANCELLED         -> terminal

Automation (enabled for v1):

  * isQuoteRequested   false->true while NEW              => advance to QUOTE_REQUESTED
  * isProductFinalized false->true while QUOTE_REQUESTED  => advance to PRODUCT_FINALIZED
  * requiresDesignServices false->true                    => create empty designServices sub-doc
  * reaching COMPLETE   => set project.closedAt + financials.projectCloseDate (if unset)
  * reaching CANCELLED  => set project.closedAt (if unset)

An automation-driven advance is applied only when the transition is legal from
the current state; otherwise the trigger flag is still stored and the status is
left unchanged. An *explicit* status in the PATCH body is always hard-validated
and raises 409 on an illegal transition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.errors import InvalidTransitionError
from app.models.common import utcnow
from app.models.enums import WorkflowState as S
from app.models.project import DesignServices, Triggers

if TYPE_CHECKING:
    from app.models.project import Project
    from app.schemas.workflow import WorkflowPatch

TRANSITIONS: dict[S, set[S]] = {
    S.NEW: {S.QUOTE_REQUESTED, S.HOLD, S.CANCELLED},
    S.QUOTE_REQUESTED: {S.PRODUCT_FINALIZED, S.HOLD, S.CANCELLED},
    S.PRODUCT_FINALIZED: {S.COMPLETE, S.HOLD, S.CANCELLED},
    S.HOLD: set(),  # computed from held_from
    S.COMPLETE: set(),
    S.CANCELLED: set(),
}


def _allowed_targets(current: S, held_from: S | None) -> set[S]:
    if current == S.HOLD:
        targets = {S.CANCELLED}
        if held_from is not None:
            targets.add(held_from)
        return targets
    return TRANSITIONS[current]


def validate_transition(current: S, target: S, held_from: S | None) -> None:
    if target == current:
        return
    if target not in _allowed_targets(current, held_from):
        raise InvalidTransitionError(
            f"Cannot transition workflow from {current.value} to {target.value}"
        )


def _transition(project: Project, target: S) -> None:
    """Hard transition — raises on an illegal move."""

    wf = project.workflow
    current = wf.status
    if target == current:
        return
    validate_transition(current, target, wf.held_from)
    wf.held_from = current if target == S.HOLD else None
    wf.status = target


def _try_transition(project: Project, target: S) -> None:
    """Automation transition — silently no-ops when illegal."""

    wf = project.workflow
    if target == wf.status:
        return
    if target in _allowed_targets(wf.status, wf.held_from):
        _transition(project, target)


def _apply_trigger_automation(project: Project, before: Triggers) -> None:
    wf = project.workflow
    now = wf.triggers

    if not before.is_quote_requested and now.is_quote_requested and wf.status == S.NEW:
        _try_transition(project, S.QUOTE_REQUESTED)

    if (
        not before.is_product_finalized
        and now.is_product_finalized
        and wf.status == S.QUOTE_REQUESTED
    ):
        _try_transition(project, S.PRODUCT_FINALIZED)

    if (
        not before.requires_design_services
        and now.requires_design_services
        and project.design_services is None
    ):
        project.design_services = DesignServices()


def _apply_terminal_side_effects(project: Project) -> None:
    wf = project.workflow
    if wf.status == S.COMPLETE:
        if project.closed_at is None:
            project.closed_at = utcnow()
        if project.financials.project_close_date is None:
            project.financials.project_close_date = utcnow().date()
    elif wf.status == S.CANCELLED:
        if project.closed_at is None:
            project.closed_at = utcnow()


def apply_workflow_update(project: Project, patch: WorkflowPatch) -> None:
    wf = project.workflow

    if patch.status is not None:
        _transition(project, patch.status)

    if patch.delivery_need_by_date is not None:
        wf.delivery_need_by_date = patch.delivery_need_by_date

    if patch.triggers is not None:
        before = wf.triggers.model_copy(deep=True)
        for key, value in patch.triggers.model_dump(exclude_unset=True).items():
            setattr(wf.triggers, key, value)
        _apply_trigger_automation(project, before)

    _apply_terminal_side_effects(project)


def reconcile_on_create(project: Project) -> None:
    """Run automation for any triggers / status supplied at creation time."""

    _apply_trigger_automation(project, Triggers())
    _apply_terminal_side_effects(project)
