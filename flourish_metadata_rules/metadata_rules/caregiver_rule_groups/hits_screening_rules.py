from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, P, register

from flourish_metadata_rules.predicates import CaregiverPredicates

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class HitsScreeningRuleGroup(CrfRuleGroup):
    hits = CrfRule(
        predicate=P('score', 'gte', 10),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.briefdangerassessment', ])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hitsscreening'
