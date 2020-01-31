"""
    Forms
    ~~~~~
"""

from flask_wtf import FlaskForm as Form
from wtforms import (
    BooleanField, TextField, TextAreaField
)
from wtforms.validators import InputRequired, ValidationError, Optional

from loris.app.wiki.utils import clean_url
from loris.app.forms.formmixin import FormMixin
from loris.app.wiki.current_wiki import current_wiki


class URLForm(Form, FormMixin):
    url = TextField(
        'url', [InputRequired()],
        description='URL of new wiki entry'
    )

    def validate_url(form, field):
        if current_wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        return clean_url(url)


class SearchForm(Form, FormMixin):
    term = TextField(
        'term',
        [InputRequired()],
        description='Search for... (regex accepted)'
    )
    ignore_case = BooleanField(
        'ignore case',
        default=True)


class EditorForm(Form, FormMixin):
    title = TextField(
        'title', [InputRequired()],
        description='title of wiki entry'
    )
    body = TextAreaField(
        'body', [InputRequired()],
        description='markdown text of wiki entry'
    )
    tags = TextField(
        'tags', [Optional()],
        description='tags'
    )
