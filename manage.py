# -*- coding:utf-8 -*-
from app import create_app,db
import os
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate,MigrateCommand
from app.models import User,Role,Permission,Post,Follow,Comment
import sys


reload(sys)
sys.setdefaultencoding('utf-8')


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app,User=User,db=db,Role=Role,
                Follow=Follow,Permission=Permission,Post=Post,Comment=Comment)
manager.add_command('shell',Shell(make_context=make_shell_context))
manager.add_command('db',MigrateCommand)


if __name__ == '__main__':
    manager.run()