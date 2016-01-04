from . import main
from flask import url_for, request, redirect, render_template, send_file, flash, abort
from .forms import RegisterAppForm, ReviewAppForm
from ..models import Authapp, User
from flask.ext.login import login_required, current_user
from .. import db


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/favicon.ico')
def favicon():
    # return redirect(url_for('static', filename='images/favicon.ico'))
    return send_file('static/images/favicon.ico', as_attachment=False)


@main.route('/apps/register', methods=['GET', 'POST'])
@login_required
def register_app():
    form = RegisterAppForm()
    if form.validate_on_submit():
        key = Authapp.generate_app_key()
        while Authapp.query.filter_by(app_key=key).first() is not None:
            key = Authapp.generate_app_key()
        secret = Authapp.generate_app_secret()
        authapp = Authapp(app_name=form.appname.data, app_url=form.appurl.data, app_description=form.appdes.data,
                          app_key=key, app_secret=secret, user_ID=current_user.user_ID)
        db.session.add(authapp)
        db.session.commit()
        flash('Your app has registered successfully')
        return redirect(url_for('main.show_authapp', appID=authapp.app_ID))
    return render_template('authapps/register_app.html', form=form)


@main.route('/apps/<int:appID>')
@login_required
def show_authapp(appID):
    app = Authapp.query.filter_by(app_ID=appID).first()
    if app is not None:
        return render_template('authapps/app.html', app=app)
    return redirect(url_for('main.index'))


@main.route('/apps')
@login_required
def show_my_apps():
    apps = Authapp.query.filter_by(user_ID=current_user.user_ID).all()
    return render_template('authapps/apps.html', apps=apps)


@main.route('/apps/<int:appID>/review', methods=['GET', 'POST'])
@login_required
def show_review_app(appID):
    if not current_user.is_administrator():
        abort(403)
    app = Authapp.query.filter_by(app_ID=appID).first()
    if app is None:
        abort(404)
    form = ReviewAppForm()
    if form.validate_on_submit():
        app.app_status = True
        db.session.add(app)
        db.session.commit()
        flash('App has been approved')
        return redirect(url_for('main.show_authapp', appID=appID))
    user = User.query.filter_by(user_ID=app.user_ID).first()
    return render_template('authapps/review_app.html', form=form, user=user, app=app)


@main.route('/user/<int:uid>')
@login_required
def show_user_profile(uid):
    if not current_user.is_administrator() and current_user.user_ID != uid:
        abort(403)
    user = User.query.get(uid)
    if user:
        return render_template('auth/user.html', user=user)
    abort(404)
