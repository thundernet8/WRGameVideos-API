# coding=utf-8
from __future__ import unicode_literals
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, Field
from wtforms.validators import Required, Length, Email, EqualTo, Regexp, URL
from ..exceptions import ValidationError


class OpenLoginForm(Form):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required(), Length(6)])
    submit = SubmitField('Authorize Login')