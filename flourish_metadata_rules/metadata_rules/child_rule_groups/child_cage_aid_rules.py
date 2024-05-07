from edc_metadata_rules import CrfRule, CrfRuleGroup, register
from edc_metadata import NOT_REQUIRED, REQUIRED
from flourish_metadata_rules.predicates import ChildPredicates

app_label = 'flourish_child'
pc = ChildPredicates()


@register()
class ChildCageAidRuleGroup(CrfRuleGroup):
    cage_aid = CrfRule(
        predicate=pc.func_child_social_work_referral_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childsocialworkreferral'],
    )

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.childcageaid'
