from edc_constants.constants import YES, PARTICIPANT
from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, P, register

from ...predicates import ChildPredicates

app_label = 'flourish_child'
pc = ChildPredicates()


@register()
class ChildVisitRuleGroup(CrfRuleGroup):

    child_clinician_notes = CrfRule(
        predicate=P('info_source', 'eq', PARTICIPANT),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childcliniciannotes'])

    birth_exam = CrfRule(
        predicate=P('is_present', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.birthexam', ])

    birth_data_rule = CrfRule(
        predicate=pc.func_birth_data_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.birthdata', ])

    mother_pregnant_pos = CrfRule(
        predicate=pc.func_mother_preg_pos,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infantarvexposure', ])

    arv_proph_quart = CrfRule(
        predicate=pc.func_arv_proph_quart,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infantarvprophylaxis', ])

    older_than_6 = CrfRule(
        predicate=pc.func_cbcl_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childcbclsection1',
                       f'{app_label}.childcbclsection2',
                       f'{app_label}.childcbclsection3',
                       f'{app_label}.childcbclsection4', ])

    older_than_7 = CrfRule(
        predicate=pc.func_7_years_older,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childtannerstaging', ])

    penncnb_ot_7 = CrfRule(
        predicate=pc.func_penncnb_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childpenncnb', ])

    female_older_12 = CrfRule(
        predicate=pc.func_12_years_older_female,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childpregtesting'])

    older_than_12 = CrfRule(
        predicate=pc.func_12_years_older,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childphqdepressionscreening',
                       f'{app_label}.childgadanxietyscreening', ])

    older_than_11 = CrfRule(
        predicate=pc.func_brief2_self_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.brief2selfreported', ])

    older_than_15_cage = CrfRule(
        predicate=pc.func_cage_aid_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childcageaid', ])

    brief_parent_exists = CrfRule(
        predicate=pc.func_brief2_parent_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.brief2parent', ])

    younger_than_36months = CrfRule(
        predicate=pc.func_36_months_younger,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infantfeeding', ])

    continued_consent_ready = CrfRule(
        predicate=pc.func_continued_consent,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childworkingstatus', ])

    forth_eighth_quarter = CrfRule(
        predicate=pc.func_forth_eighth_quarter,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childfoodsecurityquestionnaire', ])

    child_gad_anxiety_post_referral = CrfRule(
        predicate=pc.func_gad_post_referral_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childgadpostreferral'])

    child_phq_screening_post_referral = CrfRule(
        predicate=pc.func_phq9_post_referral_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childphqpostreferral'])

    adol_tb_results = CrfRule(
        predicate=pc.func_tb_lab_results_exist,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.tblabresultsadol', ]
    )

    child_tb_referral_outcome = CrfRule(
        predicate=pc.func_child_tb_referral_outcome,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childtbreferraloutcome', ]
    )

    infant_hiv_testing = CrfRule(
        predicate=pc.func_hiv_infant_testing,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.infanthivtesting', ])

    safi_stigma = CrfRule(
        predicate=pc.func_heu_status_disclosed,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childsafistigma', ])

    rapid_hiv_test = CrfRule(
        predicate=pc.func_rapid_hiv_testing_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childhivrapidtestcounseling', ])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.childvisit'
