from flourish_metadata_rules.predicates import CaregiverPredicates

from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class TbScheduleRuleGroup(CrfRuleGroup):
    tb_referral = CrfRule(
        predicate=pc.func_tb_referral,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.tbreferral', ])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.tbvisitscreeningwomen'
