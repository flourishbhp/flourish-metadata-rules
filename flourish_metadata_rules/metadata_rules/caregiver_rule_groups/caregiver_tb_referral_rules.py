from edc_constants.constants import YES
from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, P, register

from ...predicates import CaregiverPredicates

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class CaregiverTBReferralRuleGroup(CrfRuleGroup):
    caregiver_tb_screening_referral = CrfRule(
        predicate=P('referred_for_screening', '==', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.caregivertbreferraloutcome'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.tbreferralcaregiver'
