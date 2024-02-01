from dateutil.relativedelta import FR, MO, SA, SU, TH, TU, WE
from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings
from edc_data_manager.apps import AppConfig as BaseEdcDataManagerAppConfig
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
            'pre_flourish': (
                'pre_flourish_visit', 'pre_flourish.preflourishvisit'),
            'flourish_facet': (
                'facet_visit', 'flourish_facet.facetvisit'), }


    class EdcDataManagerAppConfig(BaseEdcDataManagerAppConfig):
        extra_assignee_choices = {
            'td_clinic': [
                ('clinic', 'Clinic'),
                ['gmasasa@bhp.org.bw']],
            'se_dmc': [
                ('se_dmc', 'SE & DMC'),
                ['adiphoko@bhp.org.bw', 'ckgathi@bhp.org.bw', 'imosweu@bhp.org.bw',
                 'mchawawa@bhp.org.bw']]}
        child_subject = True


    class EdcFacilityAppConfig(BaseEdcFacilityAppConfig):
        country = 'botswana'
        definitions = {
            '7-day clinic': dict(days=[MO, TU, WE, TH, FR, SA, SU],
                                 slots=[100, 100, 100, 100, 100, 100, 100]),
            '5-day clinic': dict(days=[MO, TU, WE, TH, FR],
                                 slots=[100, 100, 100, 100, 100])}
