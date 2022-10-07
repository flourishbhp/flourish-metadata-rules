from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRule, CrfRuleGroup, register, P

app_label = 'flourish_caregiver'


@register()
class TbInterviewRuleGroup(CrfRuleGroup):

    translation = CrfRule(
        predicate=P('interview_language', 'eq', 'setswana'),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.tbinterviewtranslation'])

    transcription = CrfRule(
        predicate=P('interview_language', 'eq', 'english'),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.tbinterviewtranscription'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.tbinterview'
