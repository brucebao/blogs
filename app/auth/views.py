# -*- coding:utf-8 -*-
from flask import render_template, redirect, request, url_for, flash,session
from flask.ext.login import login_user, logout_user, login_required,current_user
from . import auth
from ..models import User
from .forms import LoginForm, RegisterForm, ChangePasswordForm,PasswordResetRequestForm,\
PasswordResetForm,ChangeEmailForm
from .. import db
from ..email import send_email

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已经退出登录.')
    return redirect(url_for('main.index'))


@auth.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data,
                    )
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email,'激活账户',
                   'auth/email/confirm',user=current_user,token=token)
        flash('激活邮件已发往您的邮箱，请登录邮箱确认。')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('您已经激活了账户！')
    else:
        flash('未成功激活')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email,'激活账户',
                   'auth/email/confirm',user=current_user,token=token)
    flash('激活邮件已发往您的邮箱，请登录邮箱确认。')
    return redirect(url_for('main.index'))

@auth.route('/change_password',methods=['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            flash('密码修改成功')
            return redirect(url_for('main.index'))
        else:
            flash('密码错误')
    return render_template("auth/change_password.html",form=form)

@auth.route('/password_reset',methods=['GET','POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email,'重设密码',
                       'auth/email/reset_password',user=user,token=token)
        flash('重设密码的邮件已经发到您的邮箱')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html',form=form)


@auth.route('/password_reset/<token>',methods=['GET','POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token,form.password.data):
            flash('密码重设成功')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html',form=form)


@auth.route('/change_email',methods=['GET','POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.new_email.data
            token = current_user.generate_change_email_token(new_email)
            send_email(new_email,'确认邮箱',
                       'auth/email/change_email',token=token)
            flash('确认邮件已发到您的新邮箱')
            return redirect(url_for('main.index'))
        else:
            flash('邮箱或密码错误')
    return render_template('auth/change_email.html',form=form)


@auth.route('/change_email/<token>')
def change_email(token):
    if current_user.change_email(token):
        flash('邮箱修改成功')
    else:
        flash('邮箱修改失败')
    return redirect(url_for('main.index'))


