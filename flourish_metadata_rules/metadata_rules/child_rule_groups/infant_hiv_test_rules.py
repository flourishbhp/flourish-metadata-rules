from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register

from ...predicates import ChildPredicates

app_label = 'flourish_child'
pc = ChildPredicates()


@register()
class InfantHIVTestRuleGroup(CrfRuleGroup):
    birth_hiv_testing = CrfRule(
        predicate=pc.hiv_test_birth_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infanthivtestingbirth', ])

    other_hiv_testing = CrfRule(
        predicate=pc.hiv_test_other_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infanthivtestingother', ])

    hiv_testing_18months = CrfRule(
        predicate=pc.hiv_test_18_months_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infanthivtesting18months', ])

    hiv_testing_afr_brestfeeding = CrfRule(
        predicate=pc.hiv_test_after_breastfeeding_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infanthivtestingafterbreastfeeding', ])

    hiv_testing_6to8_months = CrfRule(
        predicate=pc.hiv_test_6_to_8_weeks_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infanthivtestingage6to8weeks', ])

    hiv_testing_9months = CrfRule(
        predicate=pc.hiv_test_9_months_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infanthivtesting9months', ])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.infanthivtesting'
