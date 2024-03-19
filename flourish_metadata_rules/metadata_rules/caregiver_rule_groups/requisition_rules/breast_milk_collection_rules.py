from edc_constants.constants import YES
from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import P, register, RequisitionRule, RequisitionRuleGroup

from flourish_labs.caregiver_panels import breast_milk_panel
from ....predicates import CaregiverPredicates

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class BreastMilk6MonthsReqRuleGroup(RequisitionRuleGroup):
    breast_milk_panel = RequisitionRule(
        predicate=P('milk_collected', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[breast_milk_panel, ])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.breastmilk6months'
        requisition_model = f'{app_label}.caregiverrequisition'
