from ...predicates import ChildPredicates

from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register

app_label = 'flourish_child'
pc = ChildPredicates()


@register()
class InfantHIVTestRuleGroup(CrfRuleGroup):
    tb_referral = CrfRule(
        predicate=pc.func_hiv_infant_testing,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infanthivtesting', ])

    class Meta:
        app_label = app_label
    
