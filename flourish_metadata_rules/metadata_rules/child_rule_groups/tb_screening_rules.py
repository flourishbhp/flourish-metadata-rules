from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register

from flourish_metadata_rules.predicates import ChildPredicates

app_label = 'flourish_child'
pc = ChildPredicates()


@register()
class TbScreeningRules(CrfRuleGroup):
    tb_referral = CrfRule(
        predicate=pc.func_child_tb_referral_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childtbreferral', ])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.childtbscreening'
