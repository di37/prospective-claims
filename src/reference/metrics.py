"""Curated metric definitions behind ``reference/metric_classes.csv``.

Section 5.4 of the annotation manual picks a claim's default baseline from its
metric class. Flows are measured over a period and default to the same quarter a
year earlier; levels are measured at a point in time and default to the
immediately prior quarter. This module is the authored source of that mapping;
``scripts/01_build_metric_classes.py`` verifies it against the SEC and writes
the CSV.

Two rules the model enforces rather than trusting an author to remember. A metric
claiming to be in the evidence store must name a taxonomy element, and a metric
marked ambiguous must carry a justification. Both were originally conventions in
prose, which is exactly the kind of thing that decays.
"""

# region Imports
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

# endregion

# region Types
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


def flow(name: str, unit: str = "USD") -> TaxonomyElement:
    """Build an element measured over a period.

    Args:
        name: Qualified element name.
        unit: Frames unit.

    Returns:
        The element.
    """
    return TaxonomyElement(name=name, unit=unit, instantaneous=False)


def instant(name: str, unit: str = "USD") -> TaxonomyElement:
    """Build an element measured at a point in time.

    Args:
        name: Qualified element name.
        unit: Frames unit.

    Returns:
        The element.
    """
    return TaxonomyElement(name=name, unit=unit, instantaneous=True)


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


# endregion

# region Flow metrics: income statement
INCOME_STATEMENT: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        metric="revenue",
        metric_class=MetricClass.FLOW,
        elements=(flow("us-gaap:Revenues"), flow("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax")),
        elements_are_alternatives=True,
        note="Filers split between the two names after ASC 606, and Revenues coverage has been declining since. Try both.",
    ),
    MetricDefinition(metric="cost_of_revenue", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:CostOfRevenue"),)),
    MetricDefinition(
        metric="gross_profit",
        metric_class=MetricClass.FLOW,
        elements=(flow("us-gaap:GrossProfit"),),
        note="Derivable from Revenues minus CostOfRevenue through the calculation linkbase when not tagged directly.",
    ),
    MetricDefinition(metric="operating_income", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:OperatingIncomeLoss"),)),
    MetricDefinition(metric="net_income", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:NetIncomeLoss"),)),
    MetricDefinition(metric="operating_expense", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:OperatingExpenses"),)),
    MetricDefinition(metric="rd_expense", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:ResearchAndDevelopmentExpense"),)),
    MetricDefinition(metric="sga_expense", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:SellingGeneralAndAdministrativeExpense"),)),
    MetricDefinition(metric="income_tax_expense", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:IncomeTaxExpenseBenefit"),)),
    MetricDefinition(metric="interest_expense", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:InterestExpense"),)),
    MetricDefinition(metric="depreciation_amortisation", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:DepreciationDepletionAndAmortization"),)),
    MetricDefinition(
        metric="eps_basic", metric_class=MetricClass.FLOW,
        elements=(flow("us-gaap:EarningsPerShareBasic", "USD-per-shares"),),
    ),
    MetricDefinition(
        metric="eps_diluted", metric_class=MetricClass.FLOW,
        elements=(flow("us-gaap:EarningsPerShareDiluted", "USD-per-shares"),),
        note="Guidance means diluted unless it says otherwise.",
    ),
)

# endregion

# region Flow metrics: cash flow statement
CASH_FLOW: tuple[MetricDefinition, ...] = (
    MetricDefinition(metric="operating_cash_flow", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:NetCashProvidedByUsedInOperatingActivities"),)),
    MetricDefinition(metric="capex", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"),)),
    MetricDefinition(metric="share_repurchase", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:PaymentsForRepurchaseOfCommonStock"),)),
    MetricDefinition(metric="dividends_paid", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:PaymentsOfDividendsCommonStock"),)),
)

# endregion

# region Flow metrics: ratios of flows
MARGIN_NOTE = (
    "A ratio of two flows, so FLOW, compared year over year. Arguable: for a "
    "non-seasonal filer management often compares sequentially. Year over year is "
    "correct for seasonal filers and merely conservative for the rest, which is "
    "why it wins."
)

RATIOS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        metric="gross_margin", metric_class=MetricClass.FLOW,
        elements=(flow("us-gaap:GrossProfit"), flow("us-gaap:Revenues")),
        expression="GrossProfit / Revenues", ambiguous=True, note=MARGIN_NOTE,
    ),
    MetricDefinition(
        metric="operating_margin", metric_class=MetricClass.FLOW,
        elements=(flow("us-gaap:OperatingIncomeLoss"), flow("us-gaap:Revenues")),
        expression="OperatingIncomeLoss / Revenues", ambiguous=True, note=MARGIN_NOTE,
    ),
    MetricDefinition(
        metric="net_margin", metric_class=MetricClass.FLOW,
        elements=(flow("us-gaap:NetIncomeLoss"), flow("us-gaap:Revenues")),
        expression="NetIncomeLoss / Revenues", ambiguous=True, note=MARGIN_NOTE,
    ),
    MetricDefinition(
        metric="free_cash_flow", metric_class=MetricClass.FLOW,
        elements=(flow("us-gaap:NetCashProvidedByUsedInOperatingActivities"), flow("us-gaap:PaymentsToAcquirePropertyPlantAndEquipment")),
        expression="NetCashProvidedByUsedInOperatingActivities - PaymentsToAcquirePropertyPlantAndEquipment",
        ambiguous=True,
        note="The class is unambiguous; the definition is not. Operating cash flow minus capex is the common form but filers vary, and some report it as non-GAAP. Record basis ADJUSTED_NON_GAAP when the speaker qualifies it.",
    ),
)

# endregion

# region Level metrics: balance sheet
BALANCE_SHEET: tuple[MetricDefinition, ...] = (
    MetricDefinition(metric="inventory", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:InventoryNet"),)),
    MetricDefinition(metric="cash", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:CashAndCashEquivalentsAtCarryingValue"),)),
    MetricDefinition(metric="accounts_receivable", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:AccountsReceivableNetCurrent"),)),
    MetricDefinition(metric="accounts_payable", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:AccountsPayableCurrent"),)),
    MetricDefinition(metric="total_assets", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:Assets"),)),
    MetricDefinition(metric="total_liabilities", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:Liabilities"),)),
    MetricDefinition(metric="stockholders_equity", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:StockholdersEquity"),)),
    MetricDefinition(metric="current_assets", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:AssetsCurrent"),)),
    MetricDefinition(metric="current_liabilities", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:LiabilitiesCurrent"),)),
    MetricDefinition(metric="long_term_debt", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:LongTermDebtNoncurrent"),)),
    MetricDefinition(
        metric="short_term_debt", metric_class=MetricClass.LEVEL,
        elements=(instant("us-gaap:DebtCurrent"),),
        note="Sparsely tagged, so expect frequent absence rather than treating it as an error.",
    ),
    MetricDefinition(
        metric="deferred_revenue", metric_class=MetricClass.LEVEL,
        elements=(instant("us-gaap:ContractWithCustomerLiabilityCurrent"), instant("us-gaap:DeferredRevenueCurrent")),
        elements_are_alternatives=True,
        note="ASC 606 renamed this. The post-606 element does not exist before 2018 and the pre-606 one is being retired, so the two together span the study window and neither does alone.",
    ),
    MetricDefinition(
        metric="remaining_performance_obligation", metric_class=MetricClass.LEVEL,
        elements=(instant("us-gaap:RevenueRemainingPerformanceObligation"),),
        note="Mostly software and subscription filers.",
    ),
    MetricDefinition(metric="goodwill", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:Goodwill"),)),
    MetricDefinition(metric="ppe_net", metric_class=MetricClass.LEVEL, elements=(instant("us-gaap:PropertyPlantAndEquipmentNet"),)),
    MetricDefinition(
        metric="working_capital", metric_class=MetricClass.LEVEL,
        elements=(instant("us-gaap:AssetsCurrent"), instant("us-gaap:LiabilitiesCurrent")),
        expression="AssetsCurrent - LiabilitiesCurrent",
        note="A difference of two levels, so LEVEL.",
    ),
)

# endregion

# region Level metrics: flow over level ratios
MIXED_NOTE = (
    "Mixes a level numerator with a flow denominator. Classed LEVEL because "
    "management discusses working-capital efficiency sequentially, but the flow "
    "denominator makes the other choice arguable."
)

MIXED_RATIOS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        metric="days_sales_outstanding", metric_class=MetricClass.LEVEL,
        elements=(instant("us-gaap:AccountsReceivableNetCurrent"), flow("us-gaap:Revenues")),
        expression="AccountsReceivableNetCurrent / Revenues * days_in_period",
        ambiguous=True, note=MIXED_NOTE,
    ),
    MetricDefinition(
        metric="inventory_turns", metric_class=MetricClass.LEVEL,
        elements=(flow("us-gaap:CostOfRevenue"), instant("us-gaap:InventoryNet")),
        expression="CostOfRevenue / InventoryNet",
        ambiguous=True, note=MIXED_NOTE,
    ),
)

# endregion

# region Share counts, split on purpose
SHARES: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        metric="shares_outstanding", metric_class=MetricClass.LEVEL,
        elements=(instant("dei:EntityCommonStockSharesOutstanding", "shares"),),
        ambiguous=True,
        note="A count at a point in time, so LEVEL. Not the same as weighted_average_shares, which is a flow. A claim about buyback impact usually means the weighted average.",
    ),
    MetricDefinition(
        metric="weighted_average_shares", metric_class=MetricClass.FLOW,
        elements=(flow("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding", "shares"),),
        ambiguous=True,
        note="Averaged over a period, so FLOW, unlike shares_outstanding.",
    ),
)

# endregion

# region Metrics outside the evidence store
# These still carry a class, because the baseline default applies whether or not
# XBRL holds the metric. Falsifiability and evidence availability are separate
# axes, and this table speaks only to the first.
UNTAGGED: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        metric="ebitda", metric_class=MetricClass.FLOW, in_evidence_store=False,
        note="Not a GAAP concept and never tagged. Derivable from tagged components, but filers define it differently.",
    ),
    MetricDefinition(
        metric="adjusted_ebitda", metric_class=MetricClass.FLOW, in_evidence_store=False,
        note="Company-defined. Evidence availability is NON-GAAP-ONLY.",
    ),
    MetricDefinition(
        metric="adjusted_eps", metric_class=MetricClass.FLOW, in_evidence_store=False,
        note="Company-defined. Consensus estimates are usually struck on this rather than on GAAP EPS.",
    ),
    MetricDefinition(
        metric="constant_currency_revenue", metric_class=MetricClass.FLOW, in_evidence_store=False,
        note="A transform on revenue rather than a separate metric. Record as revenue with transform CONSTANT_CURRENCY and basis ADJUSTED_NON_GAAP.",
    ),
    MetricDefinition(
        metric="headcount", metric_class=MetricClass.LEVEL, in_evidence_store=False,
        note="A count at a point in time. Disclosed in the 10-K cover or business section, so evidence availability is FILING-TEXT at best.",
    ),
    MetricDefinition(
        metric="backlog", metric_class=MetricClass.LEVEL, in_evidence_store=False, ambiguous=True,
        note="A level at a point in time. Rarely tagged. Where a filer reports remaining performance obligation instead, use that metric, which is tagged.",
    ),
    MetricDefinition(
        metric="annual_recurring_revenue", metric_class=MetricClass.LEVEL, in_evidence_store=False, ambiguous=True,
        note="Named as a revenue figure but reported as an annualised run rate at a point in time, so LEVEL. Company-defined and never tagged.",
    ),
    MetricDefinition(
        metric="bookings", metric_class=MetricClass.FLOW, in_evidence_store=False,
        note="Orders taken over a period, so FLOW. Not the same as backlog, which is the level that bookings accumulate into.",
    ),
)

# endregion

# region Assembled table
METRIC_DEFINITIONS: tuple[MetricDefinition, ...] = (
    INCOME_STATEMENT + CASH_FLOW + RATIOS + BALANCE_SHEET + MIXED_RATIOS + SHARES + UNTAGGED
)

_seen = [d.metric for d in METRIC_DEFINITIONS]
if len(_seen) != len(set(_seen)):
    duplicates = sorted({m for m in _seen if _seen.count(m) > 1})
    raise ValueError(f"duplicate metric keys in METRIC_DEFINITIONS: {duplicates}")

# endregion
