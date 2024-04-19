from edc_metadata_rules import CrfRule, CrfRuleGroup, register
from edc_metadata import NOT_REQUIRED, REQUIRED
from flourish_metadata_rules.predicates import CaregiverPredicates

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class RelationshipFatherInvolvementRuleGroup(CrfRuleGroup):
    caregiver_social_work_referral = CrfRule(
        predicate=pc.func_caregiver_social_work_referral_required_relation,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.caregiversocialworkreferral'],
    )

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.relationshipfatherinvolvement'
