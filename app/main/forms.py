# -*- coding:utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField,ValidationError,TextAreaField,SelectField
from wtforms.validators import Required, Length, Email,Regexp,EqualTo
from ..models import Role,User,Category
from flask.ext.pagedown.fields import  PageDownField

class EditProfileForm(Form):
    name = StringField('真实名字', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    about_me = TextAreaField('资料详细信息')
    submit = SubmitField('提交')


class EditProfileAdminForm(Form):
    email = StringField('邮箱', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField('用户名', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('账号是否激活')
    role = SelectField('角色', coerce=int)
    name = StringField('真实名字', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    about_me = TextAreaField('资料详细信息')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('此邮箱已注册.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('此用户名已注册.')


class PostForm(Form):
    title = StringField('标题')
    body = PageDownField('别让灵感成空，快快写下来：',validators=[Required()])
    category = SelectField('分类',coerce=int)
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                             for category in Category.query.order_by(Category.name).all()]


class CommentForm(Form):
    body = StringField('评论内容：',validators=[Required()])
    submit = SubmitField('提交')


class SendMessageForm(Form):
    body = StringField('私信内容', validators=[Required()])
    submit = SubmitField('发送')