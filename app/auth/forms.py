# -*- coding:utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField,ValidationError
from wtforms.validators import Required, Length, Email,Regexp,EqualTo
from ..models import User


class LoginForm(Form):
    email = StringField('邮箱', validators=[Required(), Length(1, 128),
                                             Email()])
    password = PasswordField('密码', validators=[Required()])
    remember_me = BooleanField('记住登录状态')
    submit = SubmitField('提交')


class RegisterForm(Form):
    email = StringField('邮箱', validators=[Required(), Length(1, 128),
                                             Email()])
    username = StringField('用户名', validators=[
        Required(), Length(1, 64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,
                                         '用户名只能包含字母，数字，_和.符号')])
    password = PasswordField('密码', validators=[
        Required(),EqualTo('password2',message='请重新确认密码')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('提交')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被注册')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')