import requests
from urllib.parse import urlencode
from tom_alerts.alerts import GenericAlert
from dateutil.parser import parse
from django import forms
from crispy_forms.layout import Layout, Div, Fieldset, HTML

from tom_alerts.alerts import GenericQueryForm

MARS_URL = 'https://mars.lco.global'


class MARSQueryForm(GenericQueryForm):
    time__gt = forms.CharField(required=False, label='Time Lower', widget=forms.TextInput(attrs={'type': 'date'}))
    time__lt = forms.CharField(required=False, label='Time Upper', widget=forms.TextInput(attrs={'type': 'date'}))
    jd__gt = forms.FloatField(required=False, label='JD Lower')
    jd__lt = forms.FloatField(required=False, label='JD Upper')
    filter = forms.CharField(required=False)
    cone = forms.CharField(required=False, label='Cone Search', help_text='RA,Dec,radius in degrees')
    objectcone = forms.CharField(required=False, label='Object Cone Search', help_text='Object name,radius in degrees')
    objectidps = forms.CharField(required=False, label='Nearby Objects', help_text='Id from PS1 catalog')
    ra__gt = forms.FloatField(required=False, label='RA Lower')
    ra__lt = forms.FloatField(required=False, label='RA Upper')
    dec__gt = forms.FloatField(required=False, label='Dec Lower')
    dec__lt = forms.FloatField(required=False, label='Dec Upper')
    l__gt = forms.FloatField(required=False, label='l Lower')
    l__lt = forms.FloatField(required=False, label='l Upper')
    b__gt = forms.FloatField(required=False, label='b Lower')
    b__lt = forms.FloatField(required=False, label='b Upper')
    magpsf__gte = forms.FloatField(required=False, label='Magpsf Lower')
    magpsf__lte = forms.FloatField(required=False, label='Magpsf Upper')
    sigmapsf__lte = forms.FloatField(required=False, label='Sigmapsf Upper')
    magap__gte = forms.FloatField(required=False, label='Magap Lower')
    magap__lte = forms.FloatField(required=False, label='Magap Upper')
    distnr__gte = forms.FloatField(required=False, label='Distnr Lower')
    distnr__lte = forms.FloatField(required=False, label='Distnr Upper')
    deltamaglatest__gte = forms.FloatField(required=False, label='Delta Mag Lower')
    deltamaglatest__lte = forms.FloatField(required=False, label='Delta Mag Upper')
    deltamagref__gte = forms.FloatField(required=False, label='Delta Mag Ref Lower')
    deltamagref__lte = forms.FloatField(required=False, label='Delta Mag Ref Upper')
    rb__gte = forms.FloatField(required=False, label='Real/Bogus Lower')
    classtar__gte = forms.FloatField(required=False, label='Classtar Lower')
    classtar__lte = forms.FloatField(required=False, label='Classtar Upper')
    fwhm__lte = forms.FloatField(required=False, label='FWHM Upper')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            HTML('''
                <p>Please see <a href="https://mars.lco.global/help">MARS help</a>
                for a detailed description of available filters.</p>
            '''),
            self.common_layout,
            Fieldset(
                'Time based filters',
                Div(
                    Div(
                        'time__gt',
                        'jd__gt',
                        css_class='col',
                    ),
                    Div(
                        'time__lt',
                        'jd__lt',
                        css_class='col',
                    ),
                    css_class="form-row",
                )
            ),
            Fieldset(
                'Location based filters',
                'cone',
                'objectcone',
                'objectidps',
                Div(
                    Div(
                        'ra__gt',
                        'dec__gt',
                        'l__gt',
                        'b__gt',
                        css_class='col',
                    ),
                    Div(
                        'ra__lt',
                        'dec__lt',
                        'l__lt',
                        'b__lt',
                        css_class='col',
                    ),
                    css_class="form-row",
                )
            ),
            Fieldset(
                'Other Filters',
                Div(
                    Div(
                        'magpsf__gte',
                        'magap__gte',
                        'distnr__gte',
                        'deltamaglatest__gte',
                        'deltamagref__gte',
                        'classtar__gte',
                        css_class='col'
                    ),
                    Div(
                        'magpsf__lte',
                        'magap__lte',
                        'distnr__lte',
                        'deltamaglatest__lte',
                        'deltamagref__lte',
                        'classtar__lte',
                        css_class='col'
                    ),
                    css_class='form-row',
                )
            ),
            'filter',
            'sigmapsf__lte',
            'rb__gte',
            'fwhm__lte'
        )


class MARSBroker(object):
    name = 'MARS'
    form = MARSQueryForm

    @classmethod
    def clean_parameters(clazz, parameters):
        return {k: v for k, v in parameters.items() if v and k != 'page'}

    @classmethod
    def fetch_alerts(clazz, parameters):
        if not parameters.get('page'):
            parameters['page'] = 1
        args = urlencode(clazz.clean_parameters(parameters))
        url = '{0}/?page={1}&format=json&{2}'.format(MARS_URL, parameters['page'], args)
        alerts = []
        response = requests.get(url)
        response.raise_for_status()
        parsed = response.json()
        alerts = parsed['results']
        if parsed['has_next'] and parameters['page'] < 10:
            parameters['page'] += 1
            alerts += clazz.fetch_alerts(parameters)
        return [clazz.to_generic_alert(alert) for alert in alerts]

    @classmethod
    def fetch_alert(clazz, id):
        url = f'{MARS_URL}/{id}/?format=json'
        response = requests.get(url)
        response.raise_for_status()
        parsed = response.json()
        return parsed

    @classmethod
    def to_generic_alert(clazz, mars_alert):
        timestamp = parse(mars_alert['candidate']['wall_time'])
        url = '{0}/{1}/'.format(MARS_URL, mars_alert['lco_id'])

        return GenericAlert(
            timestamp=timestamp,
            url=url,
            id=mars_alert['lco_id'],
            name=mars_alert['objectId'],
            ra=mars_alert['candidate']['ra'],
            dec=mars_alert['candidate']['dec'],
            mag=mars_alert['candidate']['magpsf'],
            score=mars_alert['candidate']['rb']
        )
