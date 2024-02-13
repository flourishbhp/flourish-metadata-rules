from dateutil.relativedelta import relativedelta
from django.test import TestCase, tag
from edc_base.tests import SiteTestCaseMixin
from edc_base.utils import get_utcnow
from edc_facility.import_holidays import import_holidays
from edc_reference import LongitudinalRefset
from edc_reference.tests import ReferenceTestHelper

from .models import AntenatalEnrollment, ChildAssent, CaregiverChildConsent
from .models import MaternalDelivery, ChildDummySubjectConsent
from ..predicates import ChildPredicates


@tag('cp')
class TestChildPredicates(SiteTestCaseMixin, TestCase):
    reference_helper_cls = ReferenceTestHelper
    app_label = 'flourish_metadata_rules'
    visit_model = 'flourish_child.childvisit'
    reference_model = 'edc_reference.reference'

    @classmethod
    def setUpClass(cls):
        return super().setUpClass()

    def tearDown(self):
        super().tearDown()

    def setUp(self):
        self.subject_identifier = '111111111-10'
        self.reference_helper = self.reference_helper_cls(
            visit_model=self.visit_model,
            subject_identifier=self.subject_identifier)

        report_datetime = get_utcnow()
        self.reference_helper.create_visit(
            report_datetime=report_datetime, timepoint='1000')

        self.reference_helper.create_visit(
            report_datetime=report_datetime + relativedelta(days=1),
            timepoint='2000')
        self.reference_helper.create_visit(
            report_datetime=report_datetime + relativedelta(days=3),
            timepoint='3000')

        self.pc = ChildPredicates()
        self.pc.app_label = self.app_label
        self.pc.maternal_app_label = self.app_label
        import_holidays()

    def test_func_consent_study_pregnant(self):
        AntenatalEnrollment.objects.create(
            subject_identifier=self.subject_identifier[:-3])

        MaternalDelivery.objects.create(
            subject_identifier=self.subject_identifier[:-3],
            delivery_datetime=(get_utcnow() - relativedelta(months=5)),
            live_infants_to_register=1)

        self.assertTrue(
            self.pc.func_consent_study_pregnant(self.infant_visits[0], ))

    def test_func_specimen_storage_consent(self):
        pass

    def test_func_7_years_older(self):
        ChildAssent.objects.create(
            subject_identifier=self.subject_identifier,
            dob=(get_utcnow() - relativedelta(years=8, months=5)).date(),
            gender='M')

        CaregiverChildConsent.objects.create(
            subject_identifier=self.subject_identifier,
            child_dob=(get_utcnow() - relativedelta(years=8, months=5)).date())

        self.assertTrue(
            self.pc.func_7_years_older(self.infant_visits[0], ))

    def test_func_12_years_older(self):
        ChildAssent.objects.create(
            subject_identifier=self.subject_identifier,
            gender='M')

        CaregiverChildConsent.objects.create(
            subject_identifier=self.subject_identifier,
            child_dob=(get_utcnow() - relativedelta(years=12, months=5)).date())

        self.assertTrue(
            self.pc.func_12_years_older(self.infant_visits[0], ))
          
    def test_func_11_years_older(self):
        ChildAssent.objects.create(
            subject_identifier=self.subject_identifier,
            gender='M')

        CaregiverChildConsent.objects.create(
            subject_identifier=self.subject_identifier,
            child_dob=(get_utcnow() - relativedelta(years=11, months=5)).date())

        self.assertTrue(
            self.pc.func_11_years_older(self.infant_visits[0], ))

    def test_func_12_years_older_female(self):
        ChildAssent.objects.create(
            subject_identifier=self.subject_identifier,
            dob=(get_utcnow() - relativedelta(years=13, months=5)).date(),
            gender='F')

        ChildDummySubjectConsent.objects.create(
            subject_identifier=self.subject_identifier,
            dob=(get_utcnow() - relativedelta(years=13, months=5)).date())

        self.assertTrue(
            self.pc.func_12_years_older_female(self.infant_visits[0], ))

    def test_func_2_months_older(self):
        MaternalDelivery.objects.create(
            subject_identifier=self.subject_identifier[:-3],
            delivery_datetime=get_utcnow() - relativedelta(months=5),
            live_infants_to_register=1)

        CaregiverChildConsent.objects.create(
            subject_identifier=self.subject_identifier,
            child_dob=(get_utcnow() - relativedelta(months=5)).date())

        self.assertTrue(
            self.pc.func_2_months_older(self.infant_visits[0], ))

    @tag('t1')
    def test_func_36_months_younger(self):
        ChildDummySubjectConsent.objects.create(
            subject_identifier=self.subject_identifier,
            dob=(get_utcnow() - relativedelta(months=12)).date())

        self.assertTrue(
            self.pc.func_36_months_younger(self.infant_visits[0], ))

    @property
    def infant_visits(self):
        return LongitudinalRefset(
            subject_identifier=self.subject_identifier,
            visit_model=self.visit_model,
            name=self.visit_model,
            reference_model_cls=self.reference_model
            ).order_by('report_datetime')
