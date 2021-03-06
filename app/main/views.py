# -*- coding:utf-8 -*-
from . import main
from flask import render_template,flash,redirect,url_for,request,current_app,abort,\
    make_response,g
from ..models import User,Role,Post,Permission,Comment,Category,Message
from .forms import EditProfileForm,EditProfileAdminForm,PostForm,CommentForm,SendMessageForm
from flask.ext.login import login_required,current_user
from .. import db
from ..decorators import admin_required,permission_required
from flask.ext.sqlalchemy import get_debug_queries

@main.before_app_request
def before_request(): #定义全局变量
    g.categories=Category.query.all()
    g.hotpost = Post.query.order_by(Post.visits.desc()).all()

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query:%s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                %(query.statement,query.parameters,query.duration,query.context)
            )
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'



@main.route('/',methods=['GET','POST'])
def index():
    form = PostForm()

    # if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
    #     post = Post(title=form.title.data,
    #                 category=Category.query.get(form.category.data),
    #                 body=form.body.data,
    #                 author=current_user._get_current_object())
    #     db.session.add(post)
    #     return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed',''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
            page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items
    return render_template('index.html',posts=posts,form=form,pagination=pagination,
                           show_followed=show_followed)

@main.route('/create_post',methods=['GET','POST'])
def create_post():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(title=form.title.data,
                    category=Category.query.get(form.category.data),
                    body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    return render_template('create_post.html',form=form)

@main.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)



@main.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('资料已经更新')
        return redirect(url_for('.profile',username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',form=form)


@main.route('/edit_profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

@main.route('/category/<int:id>')
def category(id):
    category = Category.query.get_or_404(id)
    page = request.args.get('page',1,type=int)
    pagination = category.posts.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('category.html',category=category,posts=posts,pagination=pagination)

@main.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
    post = Post.query.get_or_404(id)
    post.visits += int(1)
    print 'visit plus 1'

    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post = post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('评论提交成功')
        return redirect(url_for('.post',id=post.id,page=-1))
    page = request.args.get('page',1,type=int)
    if page == -1:
        page = (post.comments.count()-1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE']+1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out = False
    )
    comments = pagination.items
    return render_template('post.html',posts=[post],form=form,
                           comments=comments,pagination=pagination,post=post)


@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
        not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.little = form.title.data
        post.category = Category.query.get(form.category.data)
        post.body = form.body.data
        db.session.add(post)
        flash('修改成功')
        return redirect(url_for('.post',id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    form.category.data = post.category_id
    return render_template('edit_post.html',form=form)

@main.route('/delete_post/<int:id>')
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if current_user == post.author:
        db.session.delete(post)
        flash('删除成功')
        db.session.commit()
    return redirect(url_for('.index'))

@main.route('/star/<int:id>')
@login_required
def star(id):
    post = Post.query.get_or_404(id)
    if current_user.staring(post):
        flash('你已经收藏了这篇文章，不能重复收藏')
        return redirect(url_for('.post',id=post.id))
    current_user.star(post)
    flash('收藏成功')
    return redirect(url_for('.post',id=post.id))

@main.route('/unstar/<int:id>')
@login_required
def unstar(id):
    post = Post.query.get_or_404(id)
    if not current_user.staring(post):
        flash('你没有收藏这边文章，不能取消收藏')
        return redirect(url_for('.post',id=post.id))
    current_user.unstar(post)
    flash('取消收藏成功')
    return redirect(url_for('.post',id=post.id))

@main.route('/profile/<username>/starposts')
@login_required
def starposts(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    starpost = user.starposts
    return render_template('starposts.html', user=user, title="收藏的文章",
                           posts=starpost)

@main.route('/send_message/<username>',methods=['GET','POST'])
@login_required
def send_message(username):
    user = User.query.filter_by(username=username).first()
    form = SendMessageForm()
    if form.validate_on_submit():
        message = Message(body=form.body.data,
                          author = current_user,
                          sendto = user)
        db.session.add(message)
        db.session.commit()
        return redirect(url_for('.profile',username=username))
    return render_template('sendmessage.html',form=form)

@main.route('/profile/<username>/showmessages')
@login_required
def showmessages(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)

    pagination = Message.query.order_by(Message.timestamp.desc()).filter_by(sendto=current_user).paginate(
        page,error_out=False
    )
    messages = pagination.items
    return render_template('showmessage.html', user=user, title="收到的私信",
                           messages=messages,page=page,pagination=pagination)

@main.route('/showmessages/<username>/unconfirmed/<int:id>')
@login_required
def showmessage_unconfirmed(id,username):
    user = User.query.filter_by(username=username).first()
    message = Message.query.get_or_404(id)
    message.confirmed = True
    db.session.add(message)
    return redirect(url_for('.showmessages',username=username))

@main.route('/showmessages/<username>confirmed/<int:id>')
@login_required
def showmessage_confirmed(id,username):
    user = User.query.filter_by(username=username).first()
    message = Message.query.get_or_404(id)
    message.confirmed = False
    db.session.add(message)
    return redirect(url_for('.showmessages',username=username))

@main.route('/message/<username>/delete/<int:id>')
@login_required
def message_delete( id ,username):
    user = User.query.filter_by(username=username).first()
    message = Message.query.get_or_404( id )
    db.session.delete(message)
    flash('私信删除成功')
    db.session.commit()
    return redirect(url_for('.showmessages',username=username))


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效用户')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('您已经关注了此用户')
        return redirect(url_for('.profile',username=username))
    current_user.follow(user)
    flash('关注成功')
    return redirect(url_for('.profile',username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效用户')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('您没有关注此用户')
        return redirect(url_for('.profile', username=username))
    current_user.unfollow(user)
    flash('您已取消对此用户的关注')
    return redirect(url_for('.profile', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效用户')
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    pagination = user.followers.paginate(
        page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False
    )
    follows = [{ 'user':item.follower,'timestamp':item.timestamp}
               for item in pagination.items]
    return render_template('followers.html',user=user,title='关注用户',
                           endpoint='.followers',pagination=pagination,follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效用户')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERED_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="粉丝",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/post_all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed','',max_age=30*24*60*60)
    return resp

@main.route('/post_followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed','1')
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page',1,type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False )
    comments = pagination.items
    return render_template('moderate.html',comments=comments,
                           pagination=pagination,page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))
