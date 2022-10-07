from dateutil.relativedelta import relativedelta
from django.test import TestCase, tag
from edc_base.tests import SiteTestCaseMixin
from edc_base.utils import get_utcnow
from edc_constants.constants import YES, POS, NEG
from edc_facility.import_holidays import import_holidays
from edc_reference import LongitudinalRefset
from edc_reference.tests import ReferenceTestHelper

from .models import HivRapidTestCounseling, MaternalVisit, Appointment, \
    CaregiverChildConsent
from .models import MaternalDataset, AntenatalEnrollment, CyhuuPreEnrollment, \
    SubjectConsent
from .models import ScreeningPriorBhpParticipants, RelationshipFatherInvolvement
from ..predicates import CaregiverPredicates


@tag('mp')
class TestMaternalPredicates(SiteTestCaseMixin, TestCase):
    reference_helper_cls = ReferenceTestHelper
    app_label = 'flourish_metadata_rules'
    pre_app_label = 'flourish_metadata_rules'
    visit_model = 'flourish_caregiver.maternalvisit'
    reference_model = 'edc_reference.reference'

    @classmethod
    def setUpClass(cls):
        return super().setUpClass()

    def tearDown(self):
        super().tearDown()

    def setUp(self):
        self.subject_identifier = '111111111'
        self.screening_identifier = '12345'
        self.reference_helper = self.reference_helper_cls(
            visit_model=self.visit_model,
            subject_identifier=self.subject_identifier)

        report_datetime = get_utcnow()
        self.reference_helper.create_visit(
            report_datetime=report_datetime, timepoint='1000M')

        self.reference_helper.create_visit(
            report_datetime=report_datetime + relativedelta(days=1),
            timepoint='2000M')
        self.reference_helper.create_visit(
            report_datetime=report_datetime + relativedelta(days=3),
            timepoint='3000M')
        self.reference_helper.create_visit(
            report_datetime=report_datetime + relativedelta(days=2),
            timepoint='2002M')
        import_holidays()

    def test_func_preg_no_prior_participation(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label

        AntenatalEnrollment.objects.create(subject_identifier=self.subject_identifier)

        self.assertTrue(
            pc.func_preg_no_prior_participation(self.maternal_visits[0], ))

    def test_func_caregiver_no_prior_participation(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label

        self.assertTrue(
            pc.func_caregiver_no_prior_participation(self.maternal_visits[0], ))

    def test_func_bio_mothers(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label
        pc.pre_app_label = self.app_label

        MaternalDataset.objects.create(subject_identifier=self.subject_identifier)
        SubjectConsent.objects.create(subject_identifier=self.subject_identifier,
                                      screening_identifier=self.screening_identifier,
                                      biological_caregiver=YES)
        appointment = Appointment.objects.create(
            subject_identifier=self.subject_identifier)
        maternal_visit = MaternalVisit.objects.create(
            appointment=appointment,
            subject_identifier=self.subject_identifier)
        CyhuuPreEnrollment.objects.create(maternal_visit=maternal_visit,
                                          biological_mother=YES)
        HivRapidTestCounseling.objects.create(maternal_visit=maternal_visit,
                                              subject_identifier=self.subject_identifier,
                                              result=NEG)

        self.assertTrue(
            pc.func_bio_mothers_hiv_cohort_a(self.maternal_visits[1], ))
    
    def test_func_bio_mothers_hiv(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label
        pc.pre_app_label = self.app_label

        MaternalDataset.objects.create(subject_identifier=self.subject_identifier)
        ScreeningPriorBhpParticipants.objects.create(
            screening_identifier=self.screening_identifier,
            flourish_participation='interested')
        SubjectConsent.objects.create(subject_identifier=self.subject_identifier,
                                      screening_identifier=self.screening_identifier,
                                      biological_caregiver=YES)
        appointment = Appointment.objects.create(
            subject_identifier=self.subject_identifier)
        maternal_visit = MaternalVisit.objects.create(
            appointment=appointment,
            subject_identifier=self.subject_identifier)
        HivRapidTestCounseling.objects.create(maternal_visit=maternal_visit,
                                              subject_identifier=self.subject_identifier,
                                              result=POS)

        self.assertTrue(
            pc.func_bio_mothers_hiv_cohort_a(self.maternal_visits[1], ))

    def test_func_pregnant_hiv(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label

        AntenatalEnrollment.objects.create(subject_identifier=self.subject_identifier)
        appointment = Appointment.objects.create(
            subject_identifier=self.subject_identifier)
        maternal_visit = MaternalVisit.objects.create(appointment=appointment,
                                                      subject_identifier=self.subject_identifier)
        HivRapidTestCounseling.objects.create(maternal_visit=maternal_visit,
                                              subject_identifier=self.subject_identifier,
                                              result=POS)

        self.assertTrue(
            pc.func_pregnant_hiv(self.maternal_visits[0], ))

    def test_func_non_pregnant_caregivers(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label

        MaternalDataset.objects.create(subject_identifier=self.subject_identifier)
        self.assertTrue(
            pc.func_non_pregnant_caregivers(self.maternal_visits[0], ))

    def test_func_newly_recruited(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label
        pc.pre_app_label = self.app_label

        appointment = Appointment.objects.create(
            subject_identifier=self.subject_identifier)
        maternal_visit = MaternalVisit.objects.create(
            appointment=appointment,
            subject_identifier=self.subject_identifier)

        CyhuuPreEnrollment.objects.create(maternal_visit=maternal_visit,
                                          biological_mother=YES)

        MaternalDataset.objects.create(subject_identifier=self.subject_identifier)
        self.assertTrue(
            pc.func_newly_recruited(self.maternal_visits[0], ))

    def test_func_LWHIV_aged_10_15a(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label
        pc.pre_app_label = self.app_label

        CaregiverChildConsent.objects.create(
            subject_identifier=self.subject_identifier,
            child_dob=get_utcnow() - relativedelta(years=12))

        self.assertTrue(
            pc.func_LWHIV_aged_10_15a(self.maternal_visits[0], ))
        
      
    def test_func_b_feeding(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label
        
        AntenatalEnrollment.objects.create(subject_identifier=self.subject_identifier)
        self.assertTrue(pc.func_show_b_feeding_form(self.maternal_visits[2], ))
    
    @tag('bio_mothers')    
    def test_func_show_hiv_test_form(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label
        pc.pre_app_label = self.app_label

        MaternalDataset.objects.create(subject_identifier=self.subject_identifier)
        ScreeningPriorBhpParticipants.objects.create(
            screening_identifier=self.screening_identifier,
            flourish_participation='interested')
        SubjectConsent.objects.create(subject_identifier=self.subject_identifier,
                                      screening_identifier=self.screening_identifier,
                                      biological_caregiver=YES)
        
        appointment = Appointment.objects.create(
            subject_identifier=self.subject_identifier)

        maternal_visit = MaternalVisit.objects.create(
            appointment=appointment,
            subject_identifier=self.subject_identifier)
        CyhuuPreEnrollment.objects.create(maternal_visit=maternal_visit,
                                          biological_mother=YES)
        
        HivRapidTestCounseling.objects.create(maternal_visit=maternal_visit,
                                              subject_identifier=self.subject_identifier,
                                              result=NEG)

        self.assertTrue(
            pc.func_show_hiv_test_form(visit=self.maternal_visits[0], )) 
           
    @tag('sfi')    
    def test_func_show_father_involvement(self):
        pc = CaregiverPredicates()
        pc.app_label = self.app_label
        
        MaternalDataset.objects.create(subject_identifier=self.subject_identifier)
        ScreeningPriorBhpParticipants.objects.create(
            screening_identifier=self.screening_identifier,
            flourish_participation='interested')
        
        SubjectConsent.objects.create(subject_identifier=self.subject_identifier,
                                      screening_identifier=self.screening_identifier,
                                      biological_caregiver=YES)
        
        appointment = Appointment.objects.create(
            subject_identifier=self.subject_identifier)
        
        maternal_visit = MaternalVisit.objects.create(
            appointment=appointment,
            subject_identifier=self.subject_identifier)
        HivRapidTestCounseling.objects.create(maternal_visit=maternal_visit,
                                              subject_identifier=self.subject_identifier,
                                              result=POS)
        
        RelationshipFatherInvolvement.objects.create(maternal_visit=maternal_visit,
                                              subject_identifier=self.subject_identifier,
                                              partner_present=YES)
        
        
        self.assertTrue(
            pc.func_show_father_involvement(visit=self.maternal_visits[1], )) 

    @property
    def maternal_visits(self):
        return LongitudinalRefset(
            subject_identifier=self.subject_identifier,
            visit_model=self.visit_model,
            name=self.visit_model,
            reference_model_cls=self.reference_model
            ).order_by('report_datetime')
