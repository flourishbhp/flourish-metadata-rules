from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register
from edc_constants.constants import PARTICIPANT
from edc_metadata_rules import P
from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, P, register

from ...predicates import CaregiverPredicates

app_label = 'flourish_caregiver'
pc = CaregiverPredicates()


@register()
class MaternalVisitRuleGroup(CrfRuleGroup):
    clinician_notes = CrfRule(
        predicate=P('info_source', 'eq', PARTICIPANT),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.cliniciannotes'])

    pregnant = CrfRule(
        predicate=pc.enrolled_pregnant,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.foodsecurityquestionnaire',
                       f'{app_label}.caregiveredinburghdeprscreening',
                       f'{app_label}.ultrasound',
                       f'{app_label}.tbhistorypreg',
                       f'{app_label}.tbscreenpreg',
                       f'{app_label}.tbpresencehouseholdmembers',
                       f'{app_label}.substanceusepriorpregnancy',
                       f'{app_label}.tbroutinehealthscreenv2', ])

    biological_with_hiv_not_preg = CrfRule(
        predicate=pc.func_bio_mother_hiv,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivviralloadandcd4', ])

    biological_with_hiv = CrfRule(
        predicate=pc.func_bio_mothers_hiv_cohort_a,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.maternalinterimidccversion2', ])

    biological_mother = CrfRule(
        predicate=pc.func_bio_mother,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.obstericalhistory',
                       f'{app_label}.caregiverclinicalmeasurements',
                       f'{app_label}.medicalhistory', ])

    hiv_no_prior = CrfRule(
        predicate=pc.func_pregnant_hiv,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.maternaldiagnoses',
                       f'{app_label}.arvsprepregnancy',
                       f'{app_label}.maternalarvduringpreg',
                       f'{app_label}.maternalarvatdelivery',
                       f'{app_label}.maternalhivinterimhx', ])

    LWHIV_10_15a = CrfRule(
        predicate=pc.func_LWHIV_aged_10_15a,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivdisclosurestatusa'])

    LWHIV_10_15b = CrfRule(
        predicate=pc.func_LWHIV_aged_10_15b,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivdisclosurestatusb', ])

    LWHIV_10_15c = CrfRule(
        predicate=pc.func_LWHIV_aged_10_15c,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivdisclosurestatusc', ])

    hiv_test = CrfRule(
        predicate=pc.func_show_hiv_test_form,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivrapidtestcounseling', ])

    post_hiv_test = CrfRule(
        predicate=pc.func_post_hiv_rapid_test,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.posthivrapidtestandconseling', ])

    breast_feeding = CrfRule(
        predicate=pc.func_show_b_feeding_form,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.breastfeedingquestionnaire', ])

    # father involvement
    father_involvement = CrfRule(
        predicate=pc.func_show_father_involvement,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.relationshipfatherinvolvement', ])

    gad_anxiety_post_referral = CrfRule(
        predicate=pc.func_gad_post_referral_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.caregivergadpostreferral'])

    phq_screening_post_referral = CrfRule(
        predicate=pc.func_phq9_post_referral_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.caregiverphqpostreferral'])

    edinburg_screening_post_referral = CrfRule(
        predicate=pc.func_edinburgh_post_referral_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.caregiveredinburghpostreferral'])

    hiv_positive = CrfRule(
        predicate=pc.func_bio_mother_hiv,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.maternalarvpostadherence']
    )

    enrol_lwhiv = CrfRule(
        predicate=pc.func_enrolment_LWHIV,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.maternalarvadherence']
    )

    caregiver_tb_referral_outcome = CrfRule(
        predicate=pc.func_caregiver_tb_referral_outcome,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.caregivertbreferraloutcome', ])

    breast_milk_crf = CrfRule(
        predicate=pc.func_show_breast_milk_crf,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.breastmilkbirth',
                       f'{app_label}.breastmilk6months'],
    )

    parent_adol_crf = CrfRule(
        predicate=pc.func_gt10_and_after_a_year,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.parentadolrelationshipscale', ])

  childhood_lead_exposure_risk = CrfRule(
        predicate=pc.func_childhood_lead_exposure_risk_required,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.childhoodleadexposurerisk', ]
    )

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.maternalvisit'
