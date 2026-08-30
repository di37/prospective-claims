"""The 49 metrics themselves, grouped as an accountant would group them.

Authored here and verified against the SEC by the build script, so a row in
``metric_classes.csv`` that appears in no group below is a row someone typed.
"""

# region Imports
from __future__ import annotations

from reference.metrics.constructors import flow, instant
from reference.metrics.models import MetricClass, MetricDefinition

# endregion

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

CASH_FLOW: tuple[MetricDefinition, ...] = (
    MetricDefinition(metric="operating_cash_flow", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:NetCashProvidedByUsedInOperatingActivities"),)),
    MetricDefinition(metric="capex", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"),)),
    MetricDefinition(metric="share_repurchase", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:PaymentsForRepurchaseOfCommonStock"),)),
    MetricDefinition(metric="dividends_paid", metric_class=MetricClass.FLOW, elements=(flow("us-gaap:PaymentsOfDividendsCommonStock"),)),
)

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

METRIC_DEFINITIONS: tuple[MetricDefinition, ...] = (
    INCOME_STATEMENT + CASH_FLOW + RATIOS + BALANCE_SHEET + MIXED_RATIOS + SHARES + UNTAGGED
)

_seen = [d.metric for d in METRIC_DEFINITIONS]
