from datetime import timedelta

from django.apps import apps as django_apps
from django.db.models import Q
from edc_base.utils import age, get_utcnow
from edc_constants.constants import FEMALE, IND, NO, OTHER, PENDING, POS, UNKNOWN, YES
from edc_metadata_rules import PredicateCollection
from edc_reference.models import Reference
from edc_visit_tracking.constants import UNSCHEDULED
from flourish_caregiver.helper_classes import MaternalStatusHelper
from flourish_child.helper_classes.utils import child_utils


class UrlMixinNoReverseMatch(Exception):
    pass


class ChildPredicates(PredicateCollection):
    app_label = 'flourish_child'
    pre_app_label = 'pre_flourish'
    maternal_app_label = 'flourish_caregiver'
    prn_app_label = 'flourish_prn'
    visit_model = f'{app_label}.childvisit'
    maternal_visit_model = 'flourish_caregiver.maternalvisit'

    tb_visit_screening_model = f'{app_label}.tbvisitscreeningadolescent'
    tb_presence_model = f'{app_label}.tbpresencehouseholdmembersadol'
    child_requisition_model = f'{app_label}.childrequisition'
    tb_lab_results_model = f'{app_label}.tblabresultsadol'
    infant_feeding_model = f'{app_label}.infantfeeding'
    infant_hiv_test_model = f'{app_label}.infanthivtesting'
    rapid_hiv_test_model = f'{app_label}.childhivrapidtestcounseling'
    tb_hivtesting_model = f'{app_label}.hivtestingadol'
    infant_arv_proph_model = f'{app_label}.infantarvprophylaxis'
    relationship_father_involvement_model = (
        f'{maternal_app_label}.relationshipfatherinvolvement')
    child_cage_aid_model = f'{app_label}.childcageaid'
    child_tb_screening_model = f'{app_label}.childtbscreening'
    missed_birth_visit_model = f'{prn_app_label}.missedbirthvisit'

    @property
    def tb_presence_model_cls(self):
        return django_apps.get_model(self.tb_presence_model)

    @property
    def maternal_visit_model_cls(self):
        return django_apps.get_model(self.maternal_visit_model)

    @property
    def child_requisition_cls(self):
        return django_apps.get_model(self.child_requisition_model)

    @property
    def tb_lab_results_cls(self):
        return django_apps.get_model(self.tb_lab_results_model)

    @property
    def tb_hivtesting_model_cls(self):
        return django_apps.get_model(self.tb_hivtesting_model)

    @property
    def tb_visit_screening_model_cls(self):
        return django_apps.get_model(self.tb_visit_screening_model)

    @property
    def infant_feeding_model_cls(self):
        return django_apps.get_model(self.infant_feeding_model)

    @property
    def infant_hiv_test_model_cls(self):
        return django_apps.get_model(self.infant_hiv_test_model)

    @property
    def rapid_hiv_test_model_cls(self):
        return django_apps.get_model(self.rapid_hiv_test_model)

    @property
    def infant_arv_proph_model_cls(self):
        return django_apps.get_model(self.infant_arv_proph_model)

    @property
    def relationship_father_involvement_model_cls(self):
        return django_apps.get_model(self.relationship_father_involvement_model)

    @property
    def child_cage_aid_model_cls(self):
        return django_apps.get_model(self.child_cage_aid_model)

    @property
    def child_tb_screening_model_cls(self):
        return django_apps.get_model(self.child_tb_screening_model)

    @property
    def missed_birth_visit_model_cls(self):
        return django_apps.get_model(self.missed_birth_visit_model)

    def func_hiv_exposed(self, visit=None, **kwargs):
        """
        Get the pregnancy status of the mother, is positive it means
        the child was exposed to HIV
        """
        if visit.visit_code_sequence == 0:
            child_subject_identifier = visit.subject_identifier
            caregiver_subject_identifier = child_utils.caregiver_subject_identifier(
                subject_identifier=child_subject_identifier)
            maternal_status_helper = MaternalStatusHelper(
                subject_identifier=caregiver_subject_identifier)
            return maternal_status_helper.hiv_status == POS

    def get_latest_maternal_hiv_status(self, visit=None):
        maternal_subject_id = child_utils.caregiver_subject_identifier(
            subject_identifier=visit.subject_identifier)
        maternal_visit = self.maternal_visit_model_cls.objects.filter(
            subject_identifier=maternal_subject_id)

        if maternal_visit:
            latest_visit = maternal_visit.latest('report_datetime')
            maternal_status_helper = MaternalStatusHelper(
                maternal_visit=latest_visit)
        else:
            maternal_status_helper = MaternalStatusHelper(
                subject_identifier=maternal_subject_id)
        return maternal_status_helper

    def mother_pregnant(self, visit=None, **kwargs):
        """Returns true if expecting
        """
        maternal_subject_id = child_utils.caregiver_subject_identifier(
            subject_identifier=visit.subject_identifier)
        enrollment_model = django_apps.get_model(
            f'{self.maternal_app_label}.antenatalenrollment')
        try:
            enrollment_model.objects.get(
                subject_identifier=maternal_subject_id)
        except enrollment_model.DoesNotExist:
            return False
        else:
            maternal_delivery_cls = django_apps.get_model(
                f'{self.maternal_app_label}.maternaldelivery')
            try:
                maternal_delivery_cls.objects.get(
                    subject_identifier=maternal_subject_id)
            except maternal_delivery_cls.DoesNotExist:
                return True
        return False

    def version_2_1(self, visit=None, **kwargs):
        """
        Returns true if the participant is enrolled under version 2.1 and is a delivery
        visit
        """
        caregiver_child_consent_cls = django_apps.get_model(
            f'{self.maternal_app_label}.caregiverchildconsent')
        consent_objs = caregiver_child_consent_cls.objects.filter(
            subject_identifier=visit.subject_identifier, ).exclude(
            Q(version='1') | Q(version='2'))

        visit_codes = ['2000D', '2002S']
        return visit.visit_code in visit_codes and visit.visit_code_sequence == 0 and \
            consent_objs.exists()

    def get_child_age(self, visit=None, **kwargs):
        """Returns child age
        """

        caregiver_child_consent_cls = django_apps.get_model(
            f'{self.maternal_app_label}.caregiverchildconsent')

        consents = caregiver_child_consent_cls.objects.filter(
            subject_identifier=visit.subject_identifier)

        if consents:
            caregiver_child_consent = consents.latest('consent_datetime')
            return age(caregiver_child_consent.child_dob, visit.report_datetime)

    def child_age_at_enrolment(self, visit):
        if not self.mother_pregnant(visit=visit) \
                and not self.func_consent_study_pregnant(visit):

            dummy_consent_cls = django_apps.get_model(
                f'{self.app_label}.childdummysubjectconsent')

            dummy_consents = dummy_consent_cls.objects.filter(
                subject_identifier=visit.subject_identifier)
            if dummy_consents:
                dummy_consent = dummy_consents.latest('consent_datetime')
                return dummy_consent.age_at_consent

    def requires_post_referral(self, model_cls, visit):

        try:
            model_obj = model_cls.objects.get(
                child_visit__subject_identifier=visit.subject_identifier,
                child_visit__visit_code=visit.visit_code[:-1] + '0',
                child_visit__visit_code_sequence=0)
        except model_cls.DoesNotExist:
            return False
        else:
            return model_obj.referred_to not in ['receiving_emotional_care', 'declined']

    def func_gad_post_referral_required(self, visit=None, **kwargs):

        gad_referral_cls = django_apps.get_model(
            f'{self.app_label}.childgadreferral')
        return self.requires_post_referral(gad_referral_cls, visit)

    def func_phq9_post_referral_required(self, visit=None, **kwargs):

        phq9_referral_cls = django_apps.get_model(
            f'{self.app_label}.childphqreferral')
        return self.requires_post_referral(phq9_referral_cls, visit)

    def func_consent_study_pregnant(self, visit=None, **kwargs):
        """Returns True if participant's mother consented to the study in pregnancy
        """
        preg_enrol = False
        consent_cls = django_apps.get_model(
            f'{self.maternal_app_label}.caregiverchildconsent')
        maternal_delivery_cls = django_apps.get_model(
            f'{self.maternal_app_label}.maternaldelivery')

        consent_objs = consent_cls.objects.filter(
            subject_identifier=visit.subject_identifier)
        maternal_subject_id = child_utils.caregiver_subject_identifier(
            subject_identifier=visit.subject_identifier)

        if consent_objs:
            preg_enrol = getattr(
                consent_objs.earliest('consent_datetime'), 'preg_enroll', False)

        try:
            maternal_delivery_cls.objects.get(
                child_subject_identifier=visit.subject_identifier,
                subject_identifier=maternal_subject_id,
                live_infants_to_register__gte=1)
        except maternal_delivery_cls.DoesNotExist:
            return False
        else:
            return preg_enrol

    def func_birth_data_required(self, visit=None, **kwargs):
        """Returns True if participant's mother consented to the study in pregnancy and
        birth data has not been entered
        """
        bith_data_model = f'{self.app_label}.birthdata'
        prev_bith_data_obj = self.previous_model(
            visit=visit, model=bith_data_model)
        missed_visit_exists = self.missed_birth_visit_model_cls.objects.filter(
            subject_identifier=visit.subject_identifier).exists()

        return (self.func_consent_study_pregnant(visit=visit)
                and not prev_bith_data_obj and not missed_visit_exists)

    def func_mother_preg_pos(self, visit=None, **kwargs):
        """ Returns True if participant's mother consented to the study in
            pregnancy and latest hiv status is POS.
        """
        hiv_status = self.get_latest_maternal_hiv_status(
            visit=visit).hiv_status
        return (self.func_consent_study_pregnant(visit=visit) and hiv_status == POS)

    def func_preg_pos_not_fu(self, visit=None, **kwargs):
        """ Returns True if enrolled pregnant, and visit is not FU.
        """
        fu_visit_codes = ['3000', '3000A', '3000B', '3000C', ]
        return self.func_mother_preg_pos(visit) and not visit.visit_code in fu_visit_codes

    def func_arv_proph_quart(self, visit=None, **kwargs):
        preg_pos = self.func_mother_preg_pos(visit)
        if visit.visit_code == '2001':
            return preg_pos
        previous_appt = self.get_previous_appt_instance(visit.appointment)
        previous_visit = getattr(previous_appt, 'visit', None)
        is_required = False
        while previous_visit:
            try:
                prev_arv_proph = self.infant_arv_proph_model_cls.objects.get(
                    child_visit=previous_visit)
            except self.infant_arv_proph_model_cls.DoesNotExist:
                is_required = True
                previous_appt = self.get_previous_appt_instance(
                    previous_visit.appointment)
                previous_visit = getattr(previous_appt, 'visit', None)
                continue
            else:
                status = prev_arv_proph.art_status
                is_required = (status == 'in_progress')
                break
        return preg_pos and is_required

    def func_specimen_storage_consent(self, visit=None, **kwargs):
        """Returns True if participant's mother consented to repository blood specimen
        storage at enrollment.
        """

        child_age = self.get_child_age(visit=visit)

        consent_cls = None
        subject_identifier = None

        if child_age < 7:
            consent_cls = django_apps.get_model(
                f'{self.maternal_app_label}.caregiverchildconsent')
            subject_identifier = visit.subject_identifier

        elif child_age >= 18:
            consent_cls = django_apps.get_model(
                f'{self.app_label}.childcontinuedconsent')
            subject_identifier = visit.subject_identifier
        else:
            consent_cls = django_apps.get_model(
                f'{self.app_label}.childassent')
            subject_identifier = visit.subject_identifier

        if consent_cls and subject_identifier:
            consent_objs = consent_cls.objects.filter(
                subject_identifier=subject_identifier)

            if consent_objs:
                consent_obj = consent_objs.latest('consent_datetime')
                return consent_obj.specimen_consent == YES
            return False

    def func_cbcl_required(self, visit=None, **kwargs):
        childcbcl_model = f'{self.app_label}.childcbclsection1'
        prev_instance = self.previous_model(
            visit=visit, model=childcbcl_model)
        return (not prev_instance and self.func_6_years_older(visit=visit))

    def func_brief2_self_required(self, visit=None, **kwargs):
        brief2self_model = f'{self.app_label}.brief2selfreported'
        prev_instance = self.previous_model(
            visit=visit, model=brief2self_model)
        return (not prev_instance and self.func_11_years_older(visit=visit))

    def func_penncnb_required(self, visit=None, **kwargs):
        penncnb_model = f'{self.app_label}.childpenncnb'
        prev_instance = self.previous_model(
            visit=visit, model=penncnb_model)
        return (not prev_instance and self.func_7_years_older(visit=visit))

    def func_brief2_parent_required(self, visit=None, **kwargs):
        brief2parent_model = f'{self.app_label}.brief2parent'
        prev_instance = self.previous_model(
            visit=visit, model=brief2parent_model)
        return not prev_instance

    def func_6_years_older(self, visit=None, **kwargs):
        """Returns true if participant is 6 years or older
        """
        child_age = self.get_child_age(visit=visit)
        return child_age.years >= 6 if child_age else False

    def func_7_years_older(self, visit=None, **kwargs):
        """Returns true if participant is 7 years or older
        """
        child_age = self.get_child_age(visit=visit)
        return child_age.years >= 7 if child_age else False

    def func_12_years_older(self, visit=None, **kwargs):
        """Returns true if participant is 12 years or older
        """
        child_age = self.get_child_age(visit=visit)
        return child_age.years >= 12 if child_age else False

    def func_11_years_older(self, visit=None, **kwargs):
        """Returns true if participant is 11 years or older
        """
        child_age = self.get_child_age(visit=visit)
        return child_age.years >= 11 if child_age else False

    def func_15_years_older(self, visit=None, **kwargs):
        """Returns true if participant is 15 years or older
        """
        child_age = self.get_child_age(visit=visit)
        return child_age.years >= 15 if child_age else False

    def func_12_years_older_female(self, visit=None, **kwargs):
        """Returns true if participant is 12 years or older
        """
        assent_model = django_apps.get_model(f'{self.app_label}.childassent')

        assent_objs = assent_model.objects.filter(
            subject_identifier=visit.subject_identifier)

        if assent_objs:
            assent_obj = assent_objs.latest('consent_datetime')

            child_age = age(assent_obj.dob, get_utcnow())
            return child_age.years >= 12 and assent_obj.gender == FEMALE

    def func_2_months_older(self, visit=None, **kwargs):
        """Returns true if participant is 2 months or older
        """
        child_age = self.get_child_age(visit=visit)
        return child_age.months >= 2 if child_age else False

    def func_36_months_younger(self, visit=None, **kwargs):
        child_age = self.get_child_age(visit=visit)
        return ((child_age.years * 12) + child_age.months) < 36 if child_age else False

    def func_continued_consent(self, visit=None, **kwargs):
        """Returns True if participant is over 18 and continued consent has been completed
        """
        continued_consent_cls = django_apps.get_model(
            f'{self.app_label}.childcontinuedconsent')

        continued_consent_objs = continued_consent_cls.objects.filter(
            subject_identifier=visit.subject_identifier)

        if continued_consent_objs:
            return True
        return False

    def previous_model(self, visit, model):
        return Reference.objects.filter(
            model=model,
            identifier=visit.appointment.subject_identifier,
            report_datetime__lt=visit.report_datetime).order_by(
            '-report_datetime').first()

    def func_forth_eighth_quarter(self, visit=None, **kwargs):
        """
        Returns true if the visit is the 4th annual quarterly call
        """
        return int(visit.visit_code[:4]) % 4 == 0

    def func_2000D(self, visit, **kwargs):
        """
        Returns True if visit is 2000D
        """
        visit_codes = ['2000D', '2002S']

        return visit.visit_code in visit_codes and visit.visit_code_sequence == 0

    def func_cough_and_fever(self, visit, **kwargs):

        try:
            tb_screening_obj = self.tb_visit_screening_model_cls.objects.get(
                child_visit=visit)

        except self.tb_visit_screening_model_cls.DoesNotExist:
            return False
        else:
            return tb_screening_obj.have_cough == YES or tb_screening_obj.fever == YES

    def func_diagnosed_with_tb(self, visit, **kwargs):
        try:
            tb_presence_obj = self.tb_presence_model_cls.objects.get(
                child_visit=visit)
        except self.tb_presence_model_cls.DoesNotExist:
            return False
        else:
            return tb_presence_obj.tb_referral == NO

    def func_lithium_heparin_collected(self, visit, **kwargs):
        """Checks if lithium heparin was collected during the
        sheduled visit"""
        result = False

        if visit.visit_code == '2100A' and visit.visit_code_sequence >= 1:
            # if the visit is unsceduled, only trigger when requisition was
            # collected from the previous visit
            try:
                requisition = self.child_requisition_cls.objects.get(
                    panel__name='lithium_heparin',
                    child_visit__subject_identifier=visit.subject_identifier,
                    child_visit__visit_code='2100A',
                    child_visit__visit_code_sequence='0'
                )
            except self.child_requisition_cls.DoesNotExist:
                pass
            else:
                result = requisition.is_drawn == NO
        elif visit.visit_code == '2100A' and visit.visit_code_sequence == 0:
            result = True

        return result or self.func_tb_lab_results_exist(visit, **kwargs)

    def func_tb_lab_results_exist(self, visit, **kwargs):

        result = False

        if visit.visit_code == '2100A' and visit.visit_code_sequence >= 1:
            # facilitate the condition for lab results
            try:
                result_obj = self.tb_lab_results_cls.objects.get(
                    child_visit__subject_identifier=visit.subject_identifier,
                    child_visit__visit_code='2100A',
                    child_visit__visit_code_sequence='0')

            except self.tb_lab_results_cls.DoesNotExist:
                pass
            else:
                if result_obj.quantiferon_result in [IND, 'invalid']:
                    result = True

        elif visit.visit_code == '2100A' and visit.visit_code_sequence == 0:
            # first visit, collect the sample, its mandetory
            result = True

        return result

    def newly_enrolled(self, visit=None, **kwargs):
        """Returns true if newly enrolled
        """
        enrollment_model = django_apps.get_model(
            f'{self.maternal_app_label}.antenatalenrollment')
        maternal_subject_id = child_utils.caregiver_subject_identifier(
            subject_identifier=visit.subject_identifier)
        try:
            enrollment_model.objects.get(
                child_subject_identifier=visit.subject_identifier,
                subject_identifier=maternal_subject_id)
        except enrollment_model.DoesNotExist:
            return False
        else:
            return True

    def func_hiv_infant_testing(self, visit=None, **kwargs):
        """
        Returns True under the following conditions:
        - The visit code is 2001 or 2003, and the caregiver is a newly enrolled woman
        living with HIV.
        - The visit code is 2002 and the child hasn't been tested for HIV in the 2001
        visit.
        - The child is still breastfeeding.
        - The child has stopped breastfeeding and the final HIV test for the infant has
        not been received 6 weeks after weaning.
        If none of these conditions are met, the function returns False.
        """
        child_subject_identifier = visit.subject_identifier

        infant_feeding_crf = self.infant_feeding_model_cls.objects.filter(
            child_visit__subject_identifier=child_subject_identifier
        ).order_by('-report_datetime').first()

        hiv_tested_in_2001 = self.infant_hiv_test_model_cls.objects.filter(
            child_visit__subject_identifier=child_subject_identifier,
            child_visit__visit_code='2001',
            child_tested_for_hiv=YES
        ).exists()

        hiv_test_6wks_post_wean = None

        if infant_feeding_crf and infant_feeding_crf.dt_weaned:
            hiv_test_6wks_post_wean = self.infant_hiv_test_model_cls.objects.filter(
                child_visit__subject_identifier=child_subject_identifier,
                received_date__gte=infant_feeding_crf.dt_weaned +
                timedelta(weeks=6)
            ).exists()

        child_age = self.get_child_age(visit=visit)

        child_age_in_months = (child_age.years * 12) + child_age.months

        hiv_status = self.get_latest_maternal_hiv_status(
            visit=visit).hiv_status

        if (hiv_status == POS and self.func_consent_study_pregnant(visit=visit)):
            if (self.newly_enrolled(visit=visit)
                    and visit.visit_code in ['2001', '2003', '3000', '3000A', '3000B',
                                             '3000C']):
                return True

            if visit.visit_code == '2002':
                return not hiv_tested_in_2001

            continuing_to_bf = getattr(
                infant_feeding_crf, 'continuing_to_bf', None)

            return continuing_to_bf == YES or (continuing_to_bf == NO and not
                                               hiv_test_6wks_post_wean)

        return False

    def func_tbhivtesting(self, visit=None, **kwargs):
        try:
            tb_hivtesting_obj = self.tb_hivtesting_model_cls.objects.get(
                child_visit=visit
            )
        except self.tb_hivtesting_model_cls.DoesNotExist:
            return False
        else:
            return (tb_hivtesting_obj.seen_by_healthcare == NO or
                    tb_hivtesting_obj.referred_for_treatment == NO)

    def func_tb_lab_results(self, visit, **kwargs):
        try:
            result_obj = self.tb_lab_results_cls.objects.get(
                child_visit=visit)

        except self.tb_lab_results_cls.DoesNotExist:
            False
        else:
            return result_obj.quantiferon_result == POS

    def func_visit_screening(self, visit, **kwargs):
        try:
            tb_screening_obj = self.tb_visit_screening_model_cls.objects.get(
                child_visit=visit)

        except self.tb_visit_screening_model_cls.DoesNotExist:
            return False
        else:
            return (tb_screening_obj.cough_duration == YES or
                    tb_screening_obj.fever_duration == YES or
                    tb_screening_obj.night_sweats == YES or
                    tb_screening_obj.weight_loss == YES)

    def func_tbreferaladol_required(self, visit=None, **kwargs):

        return self.func_tbhivtesting(visit=visit) or self.func_tb_lab_results(
            visit=visit) or self.func_visit_screening(
            visit=visit) or self.func_diagnosed_with_tb(visit=visit)

    def get_previous_appt_instance(self, appointment):

        previous_appt = appointment.__class__.objects.filter(
            subject_identifier=appointment.subject_identifier,
            timepoint__lt=appointment.timepoint,
            schedule_name__startswith=appointment.schedule_name[:7],
            visit_code_sequence=0).order_by('timepoint').last()

        return previous_appt or appointment.previous_by_timepoint

    def hiv_test_required(self, child_age, visit):
        try:
            infant_hiv_testing = self.infant_hiv_test_model_cls.objects.get(
                child_visit=visit)
        except self.infant_hiv_test_model_cls.DoesNotExist:
            return False
        else:
            return child_age in [i.short_name for i in
                                 infant_hiv_testing.test_visit.all()]

    def func_results_on_unscheduled(self, visit, model):
        model_cls = django_apps.get_model(model)
        if visit.appointment.visit_code_sequence > 0:
            previous_appt = visit.appointment.__class__.objects.get(
                subject_identifier=visit.appointment.subject_identifier,
                visit_code=visit.visit_code,
                visit_code_sequence=visit.appointment.visit_code_sequence - 1)
            try:
                prev_obj = model_cls.objects.get(
                    child_visit__appointment=previous_appt)
            except model_cls.DoesNotExist:
                return False
            else:
                no_results = [IND, PENDING, UNKNOWN]
                return prev_obj.hiv_test_result in no_results
        else:
            return False

    def hiv_test_birth_required(self, visit=None, **kwargs):
        model = 'flourish_child.infanthivtestingbirth'
        return (self.hiv_test_required('birth', visit) or
                self.func_results_on_unscheduled(model=model, visit=visit))

    def hiv_test_other_required(self, visit=None, **kwargs):
        model = 'flourish_child.infanthivtestingother'
        return (self.hiv_test_required(OTHER, visit) or
                self.func_results_on_unscheduled(model=model, visit=visit))

    def hiv_test_18_months_required(self, visit=None, **kwargs):
        model = 'flourish_child.infanthivtesting18months'
        return (self.hiv_test_required('18_months', visit) or
                self.func_results_on_unscheduled(model=model, visit=visit))

    def hiv_test_after_breastfeeding_required(self, visit=None, **kwargs):
        model = 'flourish_child.infanthivtestingafterbreastfeeding'
        return (self.hiv_test_required('after_breastfeeding', visit) or
                self.func_results_on_unscheduled(model=model, visit=visit))

    def hiv_test_6_to_8_weeks_required(self, visit=None, **kwargs):
        model = 'flourish_child.infanthivtestingage6to8weeks'
        return (self.hiv_test_required('6_to_8_weeks', visit) or
                self.func_results_on_unscheduled(model=model, visit=visit))

    def hiv_test_9_months_required(self, visit=None, **kwargs):
        model = 'flourish_child.infanthivtesting9months'
        return (self.hiv_test_required('9_months', visit) or
                self.func_results_on_unscheduled(model=model, visit=visit))

    def func_child_tb_referral_outcome(self, visit=None, **kwargs):
        """Returns true if caregiver TB referral outcome crf is required
        """
        if visit.reason == UNSCHEDULED:
            return False
        try:
            prev_referral = Reference.objects.filter(
                model=f'{self.app_label}.childtbreferral',
                report_datetime__lt=visit.report_datetime,
                identifier=visit.subject_identifier, ).latest(
                    'report_datetime')
        except Reference.DoesNotExist:
            return False
        else:
            outcome_exists = Reference.objects.filter(
                model=f'{self.app_label}.childtbreferraloutcome',
                report_datetime__gte=prev_referral.report_datetime,
                identifier=visit.subject_identifier, ).exists()
            return not outcome_exists

    def func_child_tb_referral_required(self, visit=None, **kwargs):
        """Returns true if child TB referral crf is required
        """

        try:
            instance = self.child_tb_screening_model_cls.objects.get(
                child_visit=visit
            )
        except self.child_tb_screening_model_cls.DoesNotExist:
            return False
        else:
            unscheduled = visit.visit_code_sequence > 0
            persistent = unscheduled and instance.symptomatic
            return instance.tb_diagnoses or persistent

    def func_child_tb_screening_required(self, visit=None, **kwargs):
        """ Required at all quarterly calls, and if unscheduled 2 week call
            required if symptomatic.
        """

        unscheduled = visit.visit_code_sequence > 0
        prev_instance = self.child_tb_screening_model_cls.objects.filter(
            child_visit__subject_identifier=visit.subject_identifier,
            child_visit__visit_code=visit.visit_code,
            child_visit__visit_code_sequence=0, )
        if unscheduled:
            return (prev_instance.count() > 0
                    and prev_instance[0].symptomatic and visit.reason_unscheduled == '2_weeks_tb_sec_screening')
        else:
            return True

    def func_heu_status_disclosed(self, visit, **kwargs):
        child_subject_identifier = visit.subject_identifier
        is_biological = child_utils.is_bio_mother(child_subject_identifier)

        disclosure_crfs = ['flourish_caregiver.hivdisclosurestatusa',
                           'flourish_caregiver.hivdisclosurestatusb',
                           'flourish_caregiver.hivdisclosurestatusc']

        for crf in disclosure_crfs:
            model_cls = django_apps.get_model(crf)
            disclosed_status = model_cls.objects.filter(
                associated_child_identifier=visit.subject_identifier,
                disclosed_status=YES).exists()
            if disclosed_status:
                return is_biological and self.func_hiv_exposed(visit)

    def func_child_social_work_referral_required(self, visit=None, **kwargs):
        """ Returns true if child Social _work referral crf is required.
        """
        try:
            cage_obj = self.child_cage_aid_model_cls.objects.get(
                child_visit=visit
            )
        except self.child_cage_aid_model_cls.DoesNotExist:
            pass
        else:
            return (
                cage_obj.cut_down == YES or
                cage_obj.people_reaction == YES or
                cage_obj.guilt == YES or
                cage_obj.eye_opener == YES

            )
        return False

    def func_rapid_hiv_testing_required(self, visit, **kwargs):
        prev_tests = self.rapid_hiv_test_model_cls.objects.filter(
            child_visit__subject_identifier=visit.subject_identifier,
            rapid_test_done=YES)
        if not prev_tests.exists():
            return True
        latest_test = prev_tests.latest('result_date')
        return (
            visit.report_datetime.date() - latest_test.result_date).days > 90

    def func_cage_aid_required(self, visit, **kwargs):
        """ Required if child is 15 years or older, and if previous
            instance exists, should not be within a year of each other.
        """
        gte_15years = self.func_15_years_older(visit)
        try:
            prev_instance = self.child_cage_aid_model_cls.objects.filter(
                child_visit__subject_identifier=visit.subject_identifier,
                child_visit__report_datetime__lt=visit.report_datetime).latest(
                    'report_datetime')
        except self.child_cage_aid_model_cls.DoesNotExist:
            return gte_15years
        else:
            prev_visit_dt = prev_instance.child_visit.report_datetime
            date_diff = (visit.report_datetime - prev_visit_dt).days
            if date_diff < 365:
                return False
            return gte_15years
