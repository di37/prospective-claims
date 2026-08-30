"""What a metric is: its class, the taxonomy elements it resolves to, and the
constructors that keep periodicity attached to the element rather than the metric.

Periodicity belongs to the element because a metric can name a flow and a level at
once: days sales outstanding puts receivables, an instant, over revenue, a period.
"""

# region Imports
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

# endregion

class MetricClass(StrEnum):
    """Which default baseline section 5.4 applies to a metric."""

    FLOW = "FLOW"
    LEVEL = "LEVEL"

class TaxonomyElement(BaseModel):
    """One XBRL element, with the properties needed to verify it.

    Periodicity lives here rather than on the metric because a ratio can mix the
    two. Days sales outstanding divides a balance-sheet level by an income-statement
    flow, and probing the level at a flow period returns 404.

    Attributes:
        name: Qualified element name, such as ``us-gaap:Revenues``.
        unit: Frames unit, such as ``USD``, ``USD-per-shares``, or ``shares``.
        instantaneous: Whether the element is measured at a point in time, which
            decides whether the frames probe needs the ``I`` period suffix.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    unit: str = "USD"
    instantaneous: bool = False



class MetricDefinition(BaseModel):
    """One row of the metric class table.

    Attributes:
        metric: The key an annotator writes in the resolution record.
        metric_class: FLOW or LEVEL, which selects the default baseline.
        elements: Taxonomy elements the metric is built from. Empty when the
            metric is not represented in the evidence store.
        elements_are_alternatives: Whether the elements are interchangeable names
            for the same quantity, to be tried in order, rather than components to
            be combined. Accounting standard changes create these: an ASC 606
            concept and the pre-606 name it replaced cover different halves of the
            study window.
        expression: How the elements combine, for ratios and differences. Empty
            when the metric is a single tagged value.
        in_evidence_store: Whether the metric is retrievable from XBRL at all.
        ambiguous: Whether the class assignment is genuinely arguable.
        note: Justification, required when ambiguous, otherwise optional context.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric: str = Field(min_length=1)
    metric_class: MetricClass
    elements: tuple[TaxonomyElement, ...] = ()
    elements_are_alternatives: bool = False
    expression: str = ""
    in_evidence_store: bool = True
    ambiguous: bool = False
    note: str = ""

    @model_validator(mode="after")
    def _check_consistency(self) -> "MetricDefinition":
        """Enforce the invariants that prose conventions would let rot.

        Returns:
            The validated definition.

        Raises:
            ValueError: If a stored metric names no element, an unstored metric
                names one, an ambiguous metric carries no justification, or a
                multi-element metric gives no expression combining them.
        """
        if self.in_evidence_store and not self.elements:
            raise ValueError(f"{self.metric}: in the evidence store but names no taxonomy element")
        if not self.in_evidence_store and self.elements:
            raise ValueError(f"{self.metric}: not in the evidence store but names elements")
        if self.ambiguous and not self.note:
            raise ValueError(f"{self.metric}: marked ambiguous but carries no justification")
        if len(self.elements) > 1 and not self.expression and not self.elements_are_alternatives:
            raise ValueError(f"{self.metric}: names {len(self.elements)} elements but no expression combining them")
        if self.elements_are_alternatives and self.expression:
            raise ValueError(f"{self.metric}: elements are alternatives, so an expression combining them is meaningless")
        return self
