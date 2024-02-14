from edc_constants.constants import NO
from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, P, register

from flourish_metadata_rules.predicates import CaregiverPredicates

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class TbScreeningRules(CrfRuleGroup):
    tb_referral = CrfRule(
        predicate=pc.func_caregiver_tb_referral_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.tbreferralcaregiver', ])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.caregivertbscreening'
