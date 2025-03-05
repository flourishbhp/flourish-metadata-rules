from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register, P
from ...predicates import CaregiverPredicates

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class HITReferralRuleGroup(CrfRuleGroup):

    hits_post_referral = CrfRule(
        predicate=P('referred_to', '!=', 'declined'),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hitspostreferral'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hitsreferral'
