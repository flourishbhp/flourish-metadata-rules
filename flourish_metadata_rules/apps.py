from dateutil.relativedelta import MO, TU, WE, TH, FR, SA, SU
from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings
from edc_facility.apps import AppConfig as BaseEdcFacilityAppConfig


class AppConfig(DjangoAppConfig):
    name = 'flourish_metadata_rules'


if settings.APP_NAME == 'flourish_metadata_rules':
    from edc_metadata.apps import AppConfig as MetadataAppConfig
    from edc_visit_tracking.apps import (
        AppConfig as BaseEdcVisitTrackingAppConfig)

    class EdcMetadataAppConfig(MetadataAppConfig):
        reason_field = {'flourish_caregiver.maternalvisit': 'reason',
                        'flourish_child.childvisit': 'reason'}

    class EdcVisitTrackingAppConfig(BaseEdcVisitTrackingAppConfig):
        visit_models = {
            'flourish_caregiver': ('maternal_visit', 'flourish_caregiver.maternalvisit'),
            'flourish_child': ('child_visit', 'flourish_child.childvisit'),
            'flourish_facet': (
                'facet_visit', 'flourish_facet.facetvisit'),
            'pre_flourish': (
                'pre_flourish_visit', 'pre_flourish.preflourishcaregivervisit')}

    class EdcFacilityAppConfig(BaseEdcFacilityAppConfig):
        country = 'botswana'
        definitions = {
            '7-day clinic': dict(days=[MO, TU, WE, TH, FR, SA, SU],
                                 slots=[100, 100, 100, 100, 100, 100, 100]),
            '5-day clinic': dict(days=[MO, TU, WE, TH, FR],
                                 slots=[100, 100, 100, 100, 100])}
