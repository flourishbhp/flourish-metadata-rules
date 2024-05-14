from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register
from ....predicates import ChildPredicates

app_label = 'flourish_child'
pc = ChildPredicates()


@register()
class TbLabResultsAdolRuleGroup(CrfRuleGroup):

    tb_referral_rule = CrfRule(
        predicate=pc.func_tbreferaladol_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.tbreferaladol', ])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.tblabresultsadol'
