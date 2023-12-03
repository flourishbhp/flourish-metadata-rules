from edc_metadata_rules import CrfRule, CrfRuleGroup, register, P
from edc_constants.constants import YES
from edc_metadata import NOT_REQUIRED, REQUIRED

app_label = 'flourish_caregiver'


@register()
class RelationshipFatherInvolvementRuleGroup(CrfRuleGroup):
    caregiver_social_work_referral = CrfRule(
        predicate=P('conunselling_referral', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.caregiversocialworkreferral'],
    )

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.relationshipfatherinvolvement'
