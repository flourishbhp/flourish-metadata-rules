from datetime import timedelta
from flourish_caregiver.helper_classes import MaternalStatusHelper
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.apps import apps as django_apps
from edc_base.utils import age, get_utcnow
from edc_constants.constants import FEMALE, YES, POS, NO, IND
from edc_metadata_rules import PredicateCollection
from edc_reference.models import Reference


class UrlMixinNoReverseMatch(Exception):
    pass


class ChildPredicates(PredicateCollection):
    app_label = 'flourish_child'
    pre_app_label = 'pre_flourish'
    maternal_app_label = 'flourish_caregiver'
    visit_model = f'{app_label}.childvisit'
    maternal_visit_model = 'flourish_caregiver.maternalvisit'

    tb_visit_screening_model = f'{app_label}.tbvisitscreeningadolescent'
    tb_presence_model = f'{app_label}.tbpresencehouseholdmembersadol'
    child_requisition_model = f'{app_label}.childrequisition'
    tb_lab_results_model = f'{app_label}.tblabresultsadol'
    infant_feeding_model = f'{app_label}.infantfeeding'
    infant_hiv_test_model = f'{app_label}.infanthivtesting'

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

    def func_hiv_exposed(self, visit=None, **kwargs):
        """
        Get the pregnancy status of the mother, is positive it means
        the child was exposed to HIV
        """
        if visit.visit_code_sequence == 0:
            child_subject_identifier = visit.subject_identifier
            caregiver_subject_identifier = child_subject_identifier[0:16]
            maternal_status_helper = MaternalStatusHelper(
                subject_identifier=caregiver_subject_identifier)
            return maternal_status_helper.hiv_status == POS

    def get_latest_maternal_hiv_status(self, visit=None):
        maternal_subject_id = visit.subject_identifier[:-3]
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
        enrollment_model = django_apps.get_model(
            f'{self.maternal_app_label}.antenatalenrollment')
        try:
            enrollment_model.objects.get(
                subject_identifier=visit.subject_identifier[:-3])
        except enrollment_model.DoesNotExist:
            return False
        else:
            maternal_delivery_cls = django_apps.get_model(
                f'{self.maternal_app_label}.maternaldelivery')
            try:
                maternal_delivery_cls.objects.get(
                    subject_identifier=visit.subject_identifier[:-3])
            except maternal_delivery_cls.DoesNotExist:
                return True
        return False

    def version_2_1(self, visit=None, **kwargs):
        """
        Returns true if the participant is enrolled under version 2.1 and is a delivery visit
        """
        caregiver_child_consent_cls = django_apps.get_model(
            f'{self.maternal_app_label}.caregiverchildconsent')
        try:
            caregiver_child_consent_cls.objects.get(
                subject_identifier=visit.subject_identifier,
                version='2.1')
        except caregiver_child_consent_cls.DoesNotExist:
            return False
        else:
            return visit.visit_code == '2000D' and visit.visit_code_sequence == 0

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
        child_birth_data_model = f'{self.app_label}.birthdata'

        consent_objs = consent_cls.objects.filter(
            subject_identifier=visit.subject_identifier)

        if consent_objs:
            preg_enrol = getattr(
                consent_objs.latest('consent_datetime'), 'preg_enroll', False)

        try:
            maternal_delivery_cls.objects.get(
                subject_identifier=visit.subject_identifier[:-3],
                live_infants_to_register__gte=1)
        except maternal_delivery_cls.DoesNotExist:
            return False
        else:
            previous_obj = Reference.objects.filter(
                model=child_birth_data_model,
                identifier=visit.appointment.subject_identifier,
                report_datetime__lt=visit.report_datetime).order_by(
                '-report_datetime').first()
            return False if previous_obj else preg_enrol

    def func_mother_preg_pos(self, visit=None, **kwargs):
        """ Returns True if participant's mother consented to the study in
            pregnancy and latest hiv status is POS.
        """
        hiv_status = self.get_latest_maternal_hiv_status(
            visit=visit).hiv_status
        return (self.func_consent_study_pregnant(visit=visit) and hiv_status == POS)

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
            subject_identifier = visit.subject_ifdentifier[:-3]

        elif child_age >= 18:
            consent_cls = django_apps.get_model(
                f'{self.app_label}.childcontinuedconsent')
            subject_identifier = visit.subject_ifdentifier
        else:
            consent_cls = django_apps.get_model(
                f'{self.app_label}.childassent')
            subject_identifier = visit.subject_ifdentifier

        if consent_cls and subject_identifier:
            consent_objs = consent_cls.objects.filter(
                subject_identifier=subject_identifier)

            if consent_objs:
                consent_obj = consent_objs.latest('consent_datetime')
                return consent_obj.specimen_consent == YES
            return False

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

    def func_3_months_old(self, visit=None, **kwargs):
        """
        Returns True if the participant is 3 months old
        """
        child_age = self.get_child_age(visit=visit)
        if 6 > child_age.months >= 3 and child_age.years == 0:
            model = f'{self.app_label}.infantdevscreening3months'
            return False if self.previous_model(visit=visit,
                                                model=model) else True

    def func_6_months_old(self, visit=None, **kwargs):
        """
        Returns True if the participant is 6 months old
        """
        child_age = self.get_child_age(visit=visit)
        if child_age.years == 0 and 9 > child_age.months >= 6:
            model = f'{self.app_label}.infantdevscreening6months'
            return False if self.previous_model(visit=visit,
                                                model=model) else True

    def func_9_months_old(self, visit=None, **kwargs):
        """
        Returns True if the participant is 9 months old
        """
        child_age = self.get_child_age(visit=visit)
        if child_age.years == 0 and 12 > child_age.months >= 9:
            model = f'{self.app_label}.infantdevscreening9months'
            return False if self.previous_model(visit=visit,
                                                model=model) else True

    def func_12_months_old(self, visit=None, **kwargs):
        """
        Returns True if the participant is 12 months old
        """
        child_age = self.get_child_age(visit=visit)
        if child_age.years == 1 and child_age.months < 6:
            model = f'{self.app_label}.infantdevscreening12months'
            return False if self.previous_model(visit=visit,
                                                model=model) else True

    def func_18_months_old(self, visit=None, **kwargs):
        """
        Returns True if the participant is 18 months old
        """
        child_age = self.get_child_age(visit=visit)
        if child_age.years == 1 and child_age.months >= 6:
            model = f'{self.app_label}.infantdevscreening18months'
            return False if self.previous_model(visit=visit,
                                                model=model) else True

    def func_36_months_old(self, visit=None, **kwargs):
        """
        Returns True if the participant is 36 months old
        """
        child_age = self.get_child_age(visit=visit)
        if child_age.years == 3:
            model = f'{self.app_label}.infantdevscreening36months'
            return False if self.previous_model(visit=visit,
                                                model=model) else True

    def func_60_months_old(self, visit=None, **kwargs):
        """
        Returns True if the participant is 5 years old
        """
        child_age = self.get_child_age(visit=visit)
        if child_age.years == 5:
            model = f'{self.app_label}.infantdevscreening60months'
            return False if self.previous_model(visit=visit,
                                                model=model) else True

    def func_72_months_old(self, visit=None, **kwargs):
        """
        Returns True if the participant is 6 years old
        """
        child_age = self.get_child_age(visit=visit)
        if child_age.years == 6:
            model = f'{self.app_label}.infantdevscreening72months'
            return False if self.previous_model(visit=visit,
                                                model=model) else True

    def func_forth_eighth_quarter(self, visit=None, **kwargs):
        """
        Returns true if the visit is the 4th annual quarterly call
        """
        child_age = self.get_child_age(visit=visit)

        caregiver_child_consent_cls = django_apps.get_model(
            f'{self.maternal_app_label}.caregiverchildconsent')

        consents = caregiver_child_consent_cls.objects.filter(
            subject_identifier=visit.subject_identifier)

        if child_age.years >= 3 and consents:

            caregiver_child_consent = consents.latest('consent_datetime')

            child_is_three_at_date = caregiver_child_consent.child_dob + relativedelta(
                years=3, months=0)

            if visit.report_datetime.date() >= child_is_three_at_date:
                return int(visit.visit_code[:4]) % 4 == 0

        return False

    def func_2000D(self, visit, **kwargs):
        """
        Returns True if visit is 2000D
        """

        return visit.visit_code == '2000D' and visit.visit_code_sequence == 0

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
        try:
            enrollment_model.objects.get(
                subject_identifier=visit.subject_identifier[:-3])
        except enrollment_model.DoesNotExist:
            return False
        else:
            return True

    def func_hiv_infant_testing(self, visit=None, **kwargs):
        """Returns true if the visit is 2001, 2003 and the caregiver
         is newly enrolled women living with HIV or final
         HIV test for infant is not received 6 weeks after weaning
        """
        child_subject_identifier = visit.subject_identifier
        caregiver_subject_identifier = child_subject_identifier[:-3]
        maternal_status_helper = MaternalStatusHelper(subject_identifier=caregiver_subject_identifier)

        hiv_test_for_2001 = self.infant_hiv_test_model_cls.objects.filter(
            child_visit__subject_identifier=child_subject_identifier,
            child_visit__visit_code='2001',
            child_tested_for_hiv=YES
        ).exists()

        # If the child was tested for HIV in 2001, hide crf for 2002
        if hiv_test_for_2001 and visit.visit_code == '2002':
            return False

        # Validate visit and caregiver
        valid_visit_and_caregiver = (
                maternal_status_helper.hiv_status == POS
                and self.newly_enrolled(visit=visit)
                and visit.visit_code in [
                    '2001', '2002', '2003']
        )

        # Get infant feeding CRF
        infant_feeding_crf = self.infant_feeding_model_cls.objects.filter(
            child_visit__subject_identifier=child_subject_identifier
        ).order_by('-report_datetime').first()

        valid_infant_eligibility = False

        # Validate infant eligibility
        if infant_feeding_crf:
            hiv_test_6wks_post_wean = None
            if infant_feeding_crf.dt_weaned:
                hiv_test_6wks_post_wean = self.infant_hiv_test_model_cls.objects.filter(
                    child_visit__subject_identifier=child_subject_identifier,
                    received_date__gte=infant_feeding_crf.dt_weaned + timedelta(weeks=6)
                ).first()

            valid_infant_eligibility = (infant_feeding_crf.continuing_to_bf == YES or
                                        (infant_feeding_crf.continuing_to_bf == NO and hiv_test_6wks_post_wean is None))

        return valid_visit_and_caregiver or valid_infant_eligibility
