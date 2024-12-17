import re
from datetime import date

from dateutil import relativedelta
from django.apps import apps as django_apps
from edc_base.utils import age, get_utcnow
from edc_constants.constants import IND, NEG, POS, UNK, YES
from edc_metadata_rules import PredicateCollection
from edc_reference.models import Reference
from edc_visit_tracking.constants import UNSCHEDULED
from flourish_caregiver.constants import BREASTFEED_ONLY
from flourish_caregiver.helper_classes import MaternalStatusHelper
from flourish_caregiver.helper_classes.utils import (
    get_child_subject_identifier_by_visit,
    get_schedule_names)


def get_difference(birth_date=None):
    difference = relativedelta.relativedelta(
        get_utcnow().date(), birth_date)
    return difference.years


class CaregiverPredicates(PredicateCollection):
    app_label = 'flourish_caregiver'
    pre_app_label = 'pre_flourish'
    visit_model = f'{app_label}.maternalvisit'
    caregiver_cage_aid_model = f'{app_label}.caregivercageaid'
    caregiver_tb_screening_model = f'{app_label}.caregivertbscreening'

    @property
    def caregiver_cage_aid_model_cls(self):
        return django_apps.get_model(self.caregiver_cage_aid_model)

    @property
    def caregiver_tb_screening_model_cls(self):
        return django_apps.get_model(self.caregiver_tb_screening_model)

    def func_hiv_positive(self, visit=None, **kwargs):
        """
        Get HIV Status from the rapid test results
        """
        maternal_status_helper = MaternalStatusHelper(
            maternal_visit=visit, subject_identifier=visit.subject_identifier)
        return maternal_status_helper.hiv_status == POS

    def viral_load(self, visit=None, **kwargs):
        """
        Returns true if the visit is 1000 or 200D and the caregiver is pos
        """
        return (self.func_hiv_positive(visit=visit)
                and visit.visit_code in ['1000M', '2000D']
                and visit.visit_code_sequence == 0)

    def enrolled_pregnant(self, visit=None, **kwargs):
        """Returns true if expecting
        """
        enrollment_model = django_apps.get_model(
            f'{self.app_label}.antenatalenrollment')
        child_subject_identifier = get_child_subject_identifier_by_visit(visit)
        try:
            enrollment_model.objects.get(
                subject_identifier=visit.subject_identifier,
                child_subject_identifier=child_subject_identifier)
        except enrollment_model.DoesNotExist:
            return False
        else:
            return True

    def currently_pregnant(self, visit=None, **kwargs):
        child_subject_identifier = get_child_subject_identifier_by_visit(visit)

        if self.enrolled_pregnant(visit=visit, **kwargs):
            maternal_delivery_cls = django_apps.get_model(
                f'{self.app_label}.maternaldelivery')
            try:
                maternal_delivery_cls.objects.get(
                    subject_identifier=visit.subject_identifier,
                    child_subject_identifier=child_subject_identifier)
            except maternal_delivery_cls.DoesNotExist:
                return True
        return False

    def is_child_offstudy(self, child_subject_identifier):

        offstudy_cls = django_apps.get_model('flourish_prn.childoffstudy')

        try:
            offstudy_cls.objects.get(
                subject_identifier=child_subject_identifier)
        except offstudy_cls.DoesNotExist:
            return False
        else:
            return True

    def get_onschedule_obj(self, visit):
        onschedule_model = django_apps.get_model(
            visit.appointment.schedule.onschedule_model)

        try:
            onschedule_obj = onschedule_model.objects.get(
                subject_identifier=visit.appointment.subject_identifier,
                schedule_name=visit.appointment.schedule_name
            )
        except onschedule_model.DoesNotExist:
            return None
        else:
            return onschedule_obj

    def get_child_age(self, child_subject_identifier, visit):
        if child_subject_identifier and not self.is_child_offstudy(
                child_subject_identifier):
            registered_model = django_apps.get_model(
                f'edc_registration.registeredsubject')
            try:
                registered_child = registered_model.objects.get(
                    subject_identifier=child_subject_identifier)
            except registered_model.DoesNotExist:
                raise
            else:
                child_dob = registered_child.dob
                report_datetime = visit.report_datetime
                if child_dob and child_dob < report_datetime.date():
                    return age(child_dob, report_datetime)
        return None

    def child_gt10(self, visit):
        onschedule_obj = self.get_onschedule_obj(visit)
        child_subject_identifier = None
        if 'antenatal' not in onschedule_obj.schedule_name:
            child_subject_identifier = onschedule_obj.child_subject_identifier
        child_age = self.get_child_age(child_subject_identifier, visit)
        if child_age:
            child_age = float(f'{child_age.years}.{child_age.months}')
            if 15.9 >= child_age >= 10:
                return [True, child_subject_identifier]
        return [False, child_subject_identifier]

    def func_child_age(self, visit=None, **kwargs):
        child_subject_identifier = None
        onschedule_obj = self.get_onschedule_obj(visit)
        if onschedule_obj.schedule_name:
            child_subject_identifier = onschedule_obj.child_subject_identifier
        return self.get_child_age(child_subject_identifier, visit)

    def func_child_age_gte10(self, visit, **kwargs):
        child_age = self.func_child_age(visit=visit, **kwargs)
        return child_age.years >= 10 if child_age else False

    def func_gt10_and_after_a_year(self, visit, **kwargs):
        # return child_age.years >= 10 if child_age else False
        relationship_scale_cls = django_apps.get_model(
            'flourish_caregiver.parentadolreloscaleparentmodel')
        is_gte_10 = self.func_child_age_gte10(visit, **kwargs)

        relationship_scale_objs = relationship_scale_cls.objects.filter(
            maternal_visit__subject_identifier=visit.subject_identifier)

        result = False

        # show crf if it doesn't exist at all
        if not relationship_scale_objs.exists():
            result = is_gte_10
        else:
            # show again after 4 visits from the latest
            relationship_scale_obj = relationship_scale_objs.latest(
                'report_datetime')
            visit_code = relationship_scale_obj.visit_code

            calculated_visit_code = int(
                re.search(r'\d+', visit_code).group()) + 4
            next_visit_code = f'{calculated_visit_code}{visit_code[-1]}'

            result = next_visit_code == visit.visit_code and is_gte_10

        return result

    def prior_participation(self, visit=None, **kwargs):
        maternal_dataset_model = django_apps.get_model(
            f'{self.app_label}.maternaldataset')

        prior_participation = maternal_dataset_model.objects.filter(
            subject_identifier=visit.subject_identifier)
        return True if prior_participation else False

    def func_preg_no_prior_participation(self, visit=None, **kwargs):
        """Returns true if participant is expecting and never
        participated in a BHP study for enrollment_visit.
        """
        return (self.enrolled_pregnant(visit=visit)
                and not self.prior_participation(visit=visit))

    def requires_post_referral(self, model_cls, visit):
        visit_code = visit.visit_code[:-2] + '0M'
        if self.enrolled_pregnant(visit) and '_fu' not in visit.schedule_name:
            visit_code = '1000M'
        try:
            model_obj = model_cls.objects.get(
                maternal_visit__subject_identifier=visit.subject_identifier,
                maternal_visit__visit_code=visit_code,
                maternal_visit__visit_code_sequence=0)
        except model_cls.DoesNotExist:
            return False
        else:
            is_referred = model_obj.referred_to not in ['receiving_emotional_care',
                                                        'declined']
            if visit.visit_code_sequence > 0:
                referral_dt = model_obj.report_datetime.date()
                visit_report_dt = visit.report_datetime.date()
                return (visit_report_dt - referral_dt).days >= 7 and is_referred
            return is_referred

    def func_gad_post_referral_required(self, visit=None, **kwargs):

        gad_referral_cls = django_apps.get_model(
            f'{self.app_label}.caregivergadreferral')
        return self.requires_post_referral(gad_referral_cls, visit)

    def func_phq9_post_referral_required(self, visit=None, **kwargs):

        phq9_referral_cls = django_apps.get_model(
            f'{self.app_label}.caregiverphqreferral')
        return self.requires_post_referral(phq9_referral_cls, visit)

    def func_edinburgh_post_referral_required(self, visit=None, **kwargs):

        edinburgh_referral_cls = django_apps.get_model(
            f'{self.app_label}.caregiveredinburghreferral')
        return self.requires_post_referral(edinburgh_referral_cls, visit)

    def func_caregiver_no_prior_participation(self, visit=None, **kwargs):
        """Returns true if participant is a caregiver and never participated in a BHP
        study.
        """
        return (not self.enrolled_pregnant(visit=visit)
                and not self.prior_participation(visit=visit))

    def func_bio_mother(self, visit=None, **kwargs):
        consent_cls = django_apps.get_model(f'{self.app_label}.subjectconsent')

        consent_obj = consent_cls.objects.filter(
            subject_identifier=visit.subject_identifier, ).latest('created')

        return consent_obj.biological_caregiver == YES

    def func_bio_mother_hiv(self, visit=None, maternal_status_helper=None, **kwargs):
        """Returns true if participant is non-pregnant biological mother living with HIV.
        """
        maternal_status_helper = maternal_status_helper or MaternalStatusHelper(
            maternal_visit=visit)

        return (self.func_bio_mother(visit=visit) and not self.currently_pregnant(
            visit=visit) and maternal_status_helper.hiv_status == POS)

    def func_bio_mothers_hiv_cohort_a(self, visit=None,
                                      maternal_status_helper=None, **kwargs):
        """Returns true if participant is biological mother living with HIV.
        """

        maternal_status_helper = maternal_status_helper or MaternalStatusHelper(
            maternal_visit=visit)

        cohort_a = visit.schedule_name[:2] == 'a_'

        return cohort_a and self.func_bio_mother_hiv(visit=visit)

    def func_pregnant_hiv(self, visit=None, maternal_status_helper=None, **kwargs):
        """Returns true if a newly enrolled participant is pregnant and living with HIV.
        """
        maternal_status_helper = maternal_status_helper or MaternalStatusHelper(
            maternal_visit=visit)

        return (self.enrolled_pregnant(visit=visit)
                and maternal_status_helper.hiv_status == POS)

    def func_non_pregnant_caregivers(self, visit=None, **kwargs):
        """Returns true if non pregnant.
        """
        appt_model = django_apps.get_model(
            f'edc_appointment.appointment')

        try:
            appt_obj = appt_model.objects.get(visit_code='1000M',
                                              visit_code_sequence='0',
                                              subject_identifier=visit.subject_identifier)
        except appt_model.DoesNotExist:
            return True
        else:
            return appt_obj.schedule_name != visit.appointment.schedule_name

    def func_newly_recruited(self, visit=None, **kwargs):
        cyhuu_model_cls = django_apps.get_model(
            f'{self.pre_app_label}.cyhuupreenrollment')
        try:
            cyhuu_model_cls.objects.get(
                maternal_visit__appointment__subject_identifier=visit.subject_identifier)
        except cyhuu_model_cls.DoesNotExist:
            return False
        else:
            return True

    def child_gt10_eligible(self, visit, maternal_status_helper, id_post_fix):

        maternal_status_helper = maternal_status_helper or MaternalStatusHelper(
            maternal_visit=visit)

        gt_10, child_subject_identifier = self.child_gt10(visit)

        if child_subject_identifier:
            child_exists = child_subject_identifier[-3:] in id_post_fix

            return maternal_status_helper.hiv_status == POS and gt_10 and child_exists
        return False

    def func_LWHIV_aged_10_15a(self, visit=None, maternal_status_helper=None, **kwargs):
       
        hivdisclosurestatusa_model_cls = django_apps.get_model(
            f'{self.app_label}.hivdisclosurestatusa')

        _, child_subject_identifier = self.child_gt10(visit)

        values = hivdisclosurestatusa_model_cls.objects.filter(
            associated_child_identifier=child_subject_identifier,
            disclosed_status = YES
        ).exists()

        return not values and self.child_gt10_eligible(
            visit, maternal_status_helper,
            ['-10', '-60', '-70', '-80', '-25', '-36'])

    def func_LWHIV_aged_10_15b(self, visit=None, maternal_status_helper=None, **kwargs):

        hivdisclosurestatusb_model_cls = django_apps.get_model(
            f'{self.app_label}.hivdisclosurestatusb')

        _, child_subject_identifier = self.child_gt10(visit)

        values = hivdisclosurestatusb_model_cls.objects.filter(
            associated_child_identifier=child_subject_identifier,
            disclosed_status = YES
        ).exists()

        return not values and self.child_gt10_eligible(visit,
                                                             maternal_status_helper,
                                                             ['-25', ])

    def func_LWHIV_aged_10_15c(self, visit=None, maternal_status_helper=None, **kwargs):

        hivdisclosurestatusc_model_cls = django_apps.get_model(
            f'{self.app_label}.hivdisclosurestatusc')

        _, child_subject_identifier = self.child_gt10(visit)

        values = hivdisclosurestatusc_model_cls.objects.filter(
            associated_child_identifier=child_subject_identifier,
            disclosed_status = YES
        ).exists()

        return not values and self.child_gt10_eligible(visit,
                                                             maternal_status_helper,
                                                             ['-36', ])

    def func_check_prev_post_hiv_test(self, visit):
        post_rapid_result_cls = django_apps.get_model(
            f'{self.app_label}.posthivrapidtestandconseling')

        try:
            latest_test = post_rapid_result_cls.objects.filter(
                maternal_visit__subject_identifier=visit.subject_identifier,
                rapid_test_done=YES,
                report_datetime__lt=visit.report_datetime).latest(
                    'result_date')
        except post_rapid_result_cls.DoesNotExist:
            return None
        else:
            return latest_test

    def func_check_prev_hiv_test(self, visit):
        rapid_result_cls = django_apps.get_model(
            f'{self.app_label}.hivrapidtestcounseling')

        latest_test = self.func_check_prev_post_hiv_test(visit)
        if not latest_test:
            try:
                latest_test = rapid_result_cls.objects.filter(
                    maternal_visit__subject_identifier=visit.subject_identifier,
                    rapid_test_done=YES,
                    report_datetime__lt=visit.report_datetime).latest(
                        'result_date')
            except rapid_result_cls.DoesNotExist:
                return None

        return latest_test

    def func_post_hiv_rapid_test(self, visit, **kwargs):
        maternal_helper = MaternalStatusHelper(maternal_visit=visit)

        latest_test = self.func_check_prev_hiv_test(visit)

        neg_mother = (maternal_helper.hiv_status in [NEG, IND, UNK] and
                      self.func_bio_mother(visit=visit))
        if latest_test:
            result_date = getattr(latest_test, 'result_date', None)
            return neg_mother and (
                visit.report_datetime.date() - result_date).days > 90
        return neg_mother

    def func_show_hiv_test_form(
            self, visit=None, maternal_status_helper=None, **kwargs):

        maternal_status_helper = maternal_status_helper or MaternalStatusHelper(
            visit)

        bio_mother = self.func_bio_mother(visit=visit)

        if maternal_status_helper.hiv_status != POS:
            if self.currently_pregnant(visit=visit) and visit.visit_code == '1000M':
                return True
            elif bio_mother:
                if (maternal_status_helper.hiv_status == NEG
                        and visit.visit_code == '2000M'
                        and not self.currently_pregnant(visit=visit)):
                    return True
                else:
                    latest_test = self.func_check_prev_hiv_test(visit)
                    result_date = getattr(latest_test, 'result_date', None)
                    return result_date and (
                        visit.report_datetime.date() - result_date).days > 90

        return False

    def func_tb_eligible(self, visit=None, maternal_status_helper=None, **kwargs):
        consent_model = 'subjectconsent'
        tb_consent_model = 'tbinformedconsent'
        ultrasound_model = 'ultrasound'
        tb_screening_form = 'tbstudyeligibility'
        maternal_status_helper = maternal_status_helper or MaternalStatusHelper(
            visit)
        tb_screening_form_cls = django_apps.get_model(
            f'{self.app_label}.{tb_screening_form}')
        consent_model_cls = django_apps.get_model(
            f'flourish_caregiver.{consent_model}')
        ultrasound_model_cls = django_apps.get_model(
            f'flourish_caregiver.{ultrasound_model}')
        tb_consent_model_cls = django_apps.get_model(
            f'flourish_caregiver.{tb_consent_model}')
        consent_obj = consent_model_cls.objects.filter(
            subject_identifier=visit.subject_identifier
        )
        tb_screening_form_objs = tb_screening_form_cls.objects.filter(
            maternal_visit__subject_identifier=visit.subject_identifier)
        child_subjects = list(consent_obj[0].caregiverchildconsent_set.all().values_list(
            'subject_identifier', flat=True))
        try:
            tb_consent_model_cls.objects.get(
                subject_identifier=visit.subject_identifier)
        except tb_consent_model_cls.DoesNotExist:
            if (consent_obj and get_difference(consent_obj[0].dob)
                    >= 18 and maternal_status_helper.hiv_status == POS and
                    consent_obj[0].citizen == YES):
                for child_subj in child_subjects:
                    try:
                        ultrasound_obj = ultrasound_model_cls.objects.get(
                            subject_identifier=visit.subject_identifier)
                    except ultrasound_model_cls.DoesNotExist:
                        return False
                    else:
                        child_consent = consent_obj[0].caregiverchildconsent_set.filter(
                            subject_identifier=child_subj).latest('consent_datetime')
                        if (visit.visit_code == '2000D' or visit.visit_code == '2001M') \
                                and child_consent.child_dob:
                            child_age = age(
                                child_consent.child_dob, get_utcnow())
                            child_age_in_months = ((
                                child_age.years * 12) +
                                child_age.months)
                            if child_age_in_months < 2:
                                try:
                                    last_tb_bj = tb_screening_form_objs.latest(
                                        'created')
                                except tb_screening_form_cls.DoesNotExist:
                                    return True
                                else:
                                    return (last_tb_bj.reasons_not_participating ==
                                            'still_thinking')
                        else:
                            return (ultrasound_obj.get_current_ga and
                                    ultrasound_obj.get_current_ga >= 22)
            else:
                return False
        else:
            return False

    def func_tb_referral(self, visit=None, **kwargs):
        visit_screening_cls = django_apps.get_model(
            'flourish_caregiver.tbvisitscreeningwomen')
        try:
            visit_screening = visit_screening_cls.objects.get(
                maternal_visit=visit
            )
        except visit_screening_cls.DoesNotExist:
            return False
        else:
            take_off_schedule = (
                visit_screening.have_cough == YES or
                visit_screening.cough_duration == '=>2 week' or
                visit_screening.fever == YES or
                visit_screening.night_sweats == YES or
                visit_screening.weight_loss == YES or
                visit_screening.cough_blood == YES or
                visit_screening.enlarged_lymph_nodes == YES
            )
            return take_off_schedule

    def func_show_b_feeding_form(self, visit=None, **kwargs):
        """
        Returns true if the visit is 2002M and the caregiver breastfeeding
        """
        if visit.visit_code == '2002M':
            return self.enrolled_pregnant(visit=visit)

        prev_obj = Reference.objects.filter(
            model=f'{self.app_label}.breastfeedingquestionnaire',
            report_datetime__lt=visit.report_datetime,
            identifier=visit.subject_identifier, ).exists()
        return (visit.visit_code > '2002M' and
                not prev_obj and self.enrolled_pregnant(visit))

    def func_show_father_involvement(self, visit=None, maternal_status_helper=None,
                                     **kwargs):
        """
        Returns true if the visit is the 4th annual quarterly call and the caregiver is
        HIV positive
        """
        maternal_status_helper = maternal_status_helper or MaternalStatusHelper(
            maternal_visit=visit)

        bio_mother = self.func_bio_mother(visit=visit)

        if bio_mother:
            return int(visit.visit_code[:4]) % 4 == 0

        return False

    def func_positive_prior_participant(self, visit=None, maternal_status_helper=None,
                                        **kwargs):
        """Returns true if participant is from a prior bhp participant and 
        """
        maternal_status_helper = maternal_status_helper or MaternalStatusHelper(
            maternal_visit=visit)

        return visit.visit_code != '1000M' and self.prior_participation(
            visit=visit) and self.func_hiv_positive(visit=visit)

    def func_enrolment_LWHIV(self, visit=None, **kwargs):
        """Returns true if women LWHIV and enrolment visit i.e. (1000M or 2000M)
        """
        hiv_pos = self.func_hiv_positive(visit)
        is_bio_caregiver = self.func_bio_mother(visit=visit)
        return visit.visit_code in ['1000M', '2000M'] and hiv_pos and is_bio_caregiver

    def func_interview_focus_group_interest(self, visit=None, **kwargs):
        """ Returns true if there's no previous instance of interview focus and
        interview crf
            otherwise returns false. NOTE: checks across both version 1 and 2 of the crf.
        """
        interview_focus_crfs = ['interviewfocusgroupinterest',
                                'interviewfocusgroupinterestv2']
        for interview_crf in interview_focus_crfs:
            interview_focus_cls = django_apps.get_model(
                f'{self.app_label}.{interview_crf}')
            try:
                interview_focus_cls.objects.get(
                    maternal_visit__subject_identifier=visit.subject_identifier,
                    maternal_visit__schedule_name__icontains='quart', )
            except interview_focus_cls.DoesNotExist:
                continue
            else:
                return True
        return False

    def func_caregiver_tb_referral_outcome(self, visit=None, **kwargs):
        """Returns true if caregiver TB referral outcome crf is required
        """
        if visit.reason == UNSCHEDULED:
            return False

        caregiver_referral_model_cls = django_apps.get_model(
            f'{self.app_label}.tbreferralcaregiver')
        caregiver_referral_outcoume_cls = django_apps.get_model(
            f'{self.app_label}.caregivertbreferraloutcome')
        schedule_names = get_schedule_names(visit.appointment)

        try:
            prev_referral = caregiver_referral_model_cls.objects.filter(
                maternal_visit__subject_identifier=visit.subject_identifier,
                maternal_visit__schedule_name__in=schedule_names,
                report_datetime__lt=visit.report_datetime).latest(
                    'report_datetime')
        except caregiver_referral_model_cls.DoesNotExist:
            return False
        else:
            outcome_exists = caregiver_referral_outcoume_cls.objects.filter(
                maternal_visit__subject_identifier=visit.subject_identifier,
                maternal_visit__schedule_name__in=schedule_names,
                report_datetime__gte=prev_referral.report_datetime).exists()
            return not outcome_exists

    def func_caregiver_tb_referral_required(self, visit=None, **kwargs):
        """ Returns true if caregiver has a household contact or if previous
            instance of CRF exists and caregiver symptoms still persist.
        """
        try:
            instance = self.caregiver_tb_screening_model_cls.objects.get(
                maternal_visit=visit
            )
        except self.caregiver_tb_screening_model_cls.DoesNotExist:
            return False
        else:
            unscheduled = visit.visit_code_sequence > 0
            persistent = unscheduled and instance.symptomatic
            return instance.tb_diagnoses or persistent

    def func_tb_screening_required(self, visit=None, **kwargs):
        """ Required at all quarterly calls, and if unscheduled 2 week call
            required if symptomatic.
        """
        schedule_names = get_schedule_names(visit.appointment)
        unscheduled = visit.visit_code_sequence > 0
        prev_instance = self.caregiver_tb_screening_model_cls.objects.filter(
            maternal_visit__subject_identifier=visit.subject_identifier,
            maternal_visit__schedule_name__in=schedule_names,
            maternal_visit__visit_code=visit.visit_code,
            maternal_visit__visit_code_sequence=0, )
        if unscheduled:
            return (prev_instance.count() > 0
                    and prev_instance[0].symptomatic and visit.reason_unscheduled == '2_weeks_tb_sec_screening')
        else:
            return True

    def func_caregiver_social_work_referral_required(self, visit=None, **kwargs):
        """Returns true if caregiver Social _work referral crf is required
        """
        try:
            cage_obj = self.caregiver_cage_aid_model_cls.objects.get(
                maternal_visit=visit
            )

        except self.caregiver_cage_aid_model_cls.DoesNotExist:
            pass
        else:
            return (
                cage_obj.cut_down == YES or
                cage_obj.people_reaction == YES or
                cage_obj.guilt == YES or
                cage_obj.eye_opener == YES

            )
        return False

    def func_counselling_referral(self, visit=None, **kwargs):
        """Returns true if couselling_referral is yes
        """
        relationship_with_father_cls = django_apps.get_model(
            f'{self.app_label}.relationshipfatherinvolvement')
        try:
            relationship_with_father_obj = relationship_with_father_cls.objects.get(
                maternal_visit=visit)
        except relationship_with_father_cls.DoesNotExist:
            pass
        else:
            return relationship_with_father_obj.conunselling_referral == YES
        return False

    def func_caregiver_social_work_referral_required_relation(self, visit=None, **kwargs):
        """Returns true if caregiver Social _work referral crf is required
        """
        return (self.func_caregiver_social_work_referral_required(visit=visit) or
                self.func_counselling_referral(visit=visit))

    def func_show_breast_milk_crf(self, visit=None, **kwargs):
        """ Returns true if participant is breastfeeding of breastfeeding and formula
        feeding.
        """
        child_subject_identifier = get_child_subject_identifier_by_visit(visit)

        if self.enrolled_pregnant(visit=visit, **kwargs):
            birth_form_model_cls = django_apps.get_model(
                f'{self.app_label}.maternaldelivery')
            try:
                birth_form_obj = birth_form_model_cls.objects.get(
                    subject_identifier=visit.subject_identifier,
                    child_subject_identifier=child_subject_identifier)
            except birth_form_model_cls.DoesNotExist:
                return False
            else:
                return (birth_form_obj.feeding_mode == BREASTFEED_ONLY or
                        birth_form_obj.feeding_mode == 'Both breastfeeding and formula '
                                                       'feeding')

    def func_childhood_lead_exposure_risk_required(self, visit=None, **kwargs):
        model = django_apps.get_model(
            f'{self.app_label}.childhoodleadexposurerisk')
        appointment = visit.appointment

        schedule_names = get_schedule_names(appointment)

        previous_appts = appointment.__class__.objects.filter(
            subject_identifier=appointment.subject_identifier,
            appt_datetime__lt=appointment.appt_datetime,
            schedule_name__in=schedule_names,
            visit_code_sequence=0).order_by('-timepoint_datetime')

        for apt in previous_appts:
            prev_instance = model.objects.filter(
                maternal_visit__appointment=apt)
            if not prev_instance.exists():
                continue

            prev_visit_code = prev_instance[0].maternal_visit.visit_code

            return (int(visit.visit_code[:4]) - 4) == int(prev_visit_code[:4])

        is_follow_up = '300' in visit.visit_code

        child_age = self.func_child_age(visit=visit)
        if child_age:
            child_age = child_age.years + (child_age.months / 12)

        is_valid_age = not 1 < child_age < 5 if child_age is not None else False

        return False if is_valid_age else is_follow_up

    def func_crf_required_annually(self, model_cls, visit):
        """ If previous instance exists, should not be within a year of each other.
        """
        try:
            prev_instance = model_cls.objects.filter(
                maternal_visit__subject_identifier=visit.subject_identifier,
                maternal_visit__report_datetime__lt=visit.report_datetime,
                maternal_visit__visit_schedule_name=visit.visit_schedule_name).latest(
                    'report_datetime')
        except model_cls.DoesNotExist:
            return True
        else:
            prev_visit_dt = prev_instance.maternal_visit.report_datetime
            date_diff = (visit.report_datetime - prev_visit_dt).days
            return date_diff > 365

    def func_cage_aid_required(self, visit, **kwargs):
        """ If previous instance exists, should not be within a year of each other.
        """
        model_cls = self.caregiver_cage_aid_model_cls
        return self.func_crf_required_annually(model_cls, visit)

    def func_safi_stigma_required(self, visit, **kwargs):
        model_cls = django_apps.get_model(
            f'{self.app_label}.caregiversafistigma')
        return self.func_crf_required_annually(model_cls, visit)
