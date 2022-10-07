from django.db import models
from django.db.models.deletion import PROTECT
from edc_base.model_mixins import BaseUuidModel
from edc_base.utils import age
from edc_base.utils import get_utcnow


class MaternalDataset(BaseUuidModel):

    subject_identifier = models.CharField(max_length=25)

    delivdt = models.DateField(null=True, blank=True)


class ChildDataset(BaseUuidModel):

    subject_identifier = models.CharField(max_length=25)


class ScreeningPriorBhpParticipants(BaseUuidModel):

    screening_identifier = models.CharField(max_length=25)

    flourish_participation = models.CharField(max_length=25)


class SubjectConsent(BaseUuidModel):

    consent_datetime = models.DateTimeField(
        default=get_utcnow)

    subject_identifier = models.CharField(max_length=25)

    screening_identifier = models.CharField(max_length=25)

    biological_caregiver = models.CharField(max_length=3)


class ChildAssent(BaseUuidModel):

    consent_datetime = models.DateTimeField(
        default=get_utcnow)

    subject_identifier = models.CharField(max_length=25)

    dob = models.DateField(null=True, blank=True)

    gender = models.CharField(max_length=1)


class ChildDummySubjectConsent(BaseUuidModel):

    consent_datetime = models.DateTimeField(
        default=get_utcnow)

    subject_identifier = models.CharField(max_length=25)

    dob = models.DateField(null=True, blank=True)

    @property
    def age_at_consent(self):
        """Returns a relativedelta.
        """
        if self.dob < self.consent_datetime.date():
            return age(self.dob, self.consent_datetime)
        return 0


class AntenatalEnrollment(BaseUuidModel):

    subject_identifier = models.CharField(max_length=25)


class Appointment(BaseUuidModel):

    subject_identifier = models.CharField(max_length=25)


class MaternalDelivery(BaseUuidModel):

    subject_identifier = models.CharField(max_length=25)

    delivery_datetime = models.DateTimeField(null=True, blank=True)

    live_infants_to_register = models.IntegerField()


class MaternalVisit(BaseUuidModel):

    appointment = models.ForeignKey(Appointment,
                                    on_delete=PROTECT)

    subject_identifier = models.CharField(max_length=25)


class ChildVisit(BaseUuidModel):

    appointment = models.ForeignKey(Appointment,
                                    on_delete=PROTECT)

    subject_identifier = models.CharField(max_length=25)


class CaregiverChildConsent(BaseUuidModel):

    consent_datetime = models.DateTimeField(
        default=get_utcnow)

    subject_identifier = models.CharField(max_length=25)

    child_dob = models.DateField(null=True, blank=True)


class CyhuuPreEnrollment(BaseUuidModel):

    maternal_visit = models.ForeignKey(MaternalVisit,
                                       on_delete=PROTECT)

    biological_mother = models.CharField(max_length=3)


class HivRapidTestCounseling(BaseUuidModel):

    maternal_visit = models.ForeignKey(MaternalVisit,
                                       on_delete=PROTECT)

    subject_identifier = models.CharField(max_length=25)

    result = models.CharField(max_length=3)
class RelationshipFatherInvolvement(BaseUuidModel):

    maternal_visit = models.ForeignKey(MaternalVisit,
                                       on_delete=PROTECT)

    subject_identifier = models.CharField(max_length=25)

    partner_present = models.CharField(max_length=3)
