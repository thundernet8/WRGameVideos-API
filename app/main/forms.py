# coding=utf-8
from __future__ import unicode_literals
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, Field
from wtforms.validators import Required, Length, Email, EqualTo, Regexp, URL
from ..models import Authapp
from ..exceptions import ValidationError


class RegisterAppForm(Form):
    appname = StringField('App Name', validators=[Required(), Length(4, 16), Regexp('^[一-龥a-zA-Z0-9]*$', 0, 'Usernames\
     must have only letters, numbers, or Chinese')])
    appurl = StringField('App Home', validators=[URL(), Required()], default='http://')
    appdes = TextAreaField('App Description', validators=[Required(), Length(20, 255)])
    submit = SubmitField('Register')

    # meth: validate_%field% will auto be run for the field
    def validate_appname(self, field):
        if Authapp.query.filter_by(app_name=field.data).first():
            raise ValidationError('App name already used')

    def validate_appurl(self, field):
        if Authapp.query.filter_by(app_url=field.data).first():
            raise ValidationError('Url already in use')


class ReviewAppForm(Form):
    submit = SubmitField('Approve')
