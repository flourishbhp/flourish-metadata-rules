from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register, P
from ...predicates import CaregiverPredicates

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class GAD7AnxietyScreeningRuleGroup(CrfRuleGroup):

    gad_anxiety_referral = CrfRule(
        predicate=P('anxiety_score', 'gte', 10),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.caregivergadreferral'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.caregivergadanxietyscreening'
