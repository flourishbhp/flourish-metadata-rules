from flourish_metadata_rules.predicates import CaregiverPredicates

from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class InterviewFocusGroupInterestRuleGroup(CrfRuleGroup):
    tb_referral = CrfRule(
        predicate=pc.func_interview_focus_group_interest,
        consequence=NOT_REQUIRED,
        alternative=REQUIRED,
        target_models=[f'{app_label}.interviewfocusgroupinterestv2', ])

    class Meta:
        app_label = app_label
        #source_model = f'{app_label}.interviewfocusgroupinterest'
