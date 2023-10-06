from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import RequisitionRule, RequisitionRuleGroup, register

from flourish_labs import dna_pcr_panel, stool_sample_panel, infant_pl_cytokines_panel
from flourish_labs import rectal_swab_panel, lithium_heparin_panel
from ....predicates import ChildPredicates

app_label = 'flourish_child'
pc = ChildPredicates()


@register()
class ChildVisitReqRuleGroup(RequisitionRuleGroup):

    # for dna_pcr if the newly enroled pregnant WLHIV and
    # not FU visit
    dna_pcr_panel_rule = RequisitionRule(
        predicate=pc.func_preg_pos_not_fu,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[dna_pcr_panel, ])

    #  stool sample for 2000D if the mother is negative
    stool_sample_panel_rule = RequisitionRule(
        predicate=pc.func_2000D,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[stool_sample_panel, ])

    plasma_store_panel_rule = RequisitionRule(
        predicate=pc.version_2_1,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[infant_pl_cytokines_panel,
                       rectal_swab_panel])

    lithium_heparin_panel_rule = RequisitionRule(
        predicate=pc.func_lithium_heparin_collected,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[lithium_heparin_panel,])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.childvisit'
        requisition_model = f'{app_label}.childrequisition'
