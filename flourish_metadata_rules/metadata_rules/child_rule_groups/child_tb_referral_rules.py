from edc_constants.constants import YES
from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, P, register

from ...predicates import CaregiverPredicates

app_label = 'flourish_child'
pc = CaregiverPredicates()


@register()
class ChildTBReferralRuleGroup(CrfRuleGroup):
    child_tb_screening_referral = CrfRule(
        predicate=P('referred_for_screening', '==', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childtbreferraloutcome'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.childtbreferral'
