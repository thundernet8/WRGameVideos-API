from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, EqualTo, Regexp
from ..models import User
from ..exceptions import ValidationError


class LoginForm(Form):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required(), Length(6)])
    remember = BooleanField('Keep Logged Status')
    submit = SubmitField('Login')


class RegisterForm(Form):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    username = StringField('Username', validators=[Required(), Length(1,64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password', validators=[Required(), Length(6), EqualTo('password2', message='Password must be match')])
    password2 = PasswordField('Confirm password', validators=[Required(), Length(6)])
    submit = SubmitField('Register')

    # meth: validate_%field% will auto be run for the field
    def validate_email(self, field):
        if User.query.filter_by(user_email=field.data).first():
            raise ValidationError('Email already registered')

    def validate_username(self, field):
        if User.query.filter_by(user_login=field.data).first():
            raise ValidationError('Username already in use')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('New Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match'), Length(6)])
    password2 = PasswordField('Confirm password', validators=[Required(), Length(6)])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(user_email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[Required()])
    password = PasswordField('New password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password', validators=[Required(), Length(6)])
    submit = SubmitField('Update Password')


class ChangeEmailForm(Form):
    email = StringField('New Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(user_email=field.data).first():
            raise ValidationError('Email already registered.')
