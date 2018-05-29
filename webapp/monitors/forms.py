"""Monitor Forms.

Model the forms for the monitors data model.

"""
from checks.endpoint import HTTPVerb
from flask_wtf import FlaskForm
from wtforms import Form
from wtforms import (StringField, SelectField, SubmitField, TextAreaField,
                     IntegerField, FieldList, FormField)
from wtforms.validators import DataRequired, Length


# Dynamically populate a SelectField with our HTTPVerb enum
EndpointVerbs = [
    (name, name) for name, member in HTTPVerb.__members__.items()
]
SchemeChoices = [
    ('http', 'HTTP'),
    ('https', 'HTTPS')
]


def multi_header_input_widget(field, ul_class='', **kwargs):
    print(f"field: {field}")
    print(f"kwargs: {kwargs}")


class HeaderForm(Form):
    key = StringField()
    value = StringField()


class EndpointForm(FlaskForm):
    """Form to add/modify an Endpoint Monitor."""
    name = StringField('Monitor Name',
                       validators=[DataRequired(), Length(min=3, max=128)])
    frequency = IntegerField('Monitor Frequency',
                             validators=[DataRequired()])
    scheme = SelectField('Scheme', choices=SchemeChoices,
                         validators=[DataRequired()])
    server = StringField('Server/IP',
                         validators=[DataRequired()])
    port = IntegerField('Port',
                        validators=[DataRequired()])
    path = StringField('Path/Resource')
    verb = SelectField('HTTP Verb', choices=EndpointVerbs,
                       validators=[DataRequired()])
    payload = TextAreaField('Payload')
    headers = FieldList(FormField(HeaderForm))
    submit = SubmitField('Submit It')

