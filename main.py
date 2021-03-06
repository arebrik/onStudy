# coding: utf-8
import sys

from settings import sets


if __name__ == "__main__":
    for a in ('help', '-h', '--help'):
        if a in sys.argv:
            print('''python main.py [init]\n\nCommands:
    init     - for init project on start or reinit on changed requirements.
    nodebug    - for debug in terminal.''')
            sys.exit(0)

    if 'nodebug' in sys.argv:
        sets.DEBUG = False

    if 'init' in sys.argv:
        from scripts.init import init_all
        init_all()


import log_config
import logging
log_config.load_config(debug=sets.DEBUG)
log = logging.getLogger('main')

import tornado.ioloop
import tornado.web

from handlers.MainHandler import MainHandler, WsUpdateMainHandler, RoomHandler, AboutHandler
from handlers.auth import LogoutHandler, LoginHandler, RegisterHandler
from handlers.static_handlers import CssHandler, AssetsLibHandler
from handlers.course_manager import (CreateCourseHandler, ManageCourseHandler, CoursesHandler, HomeWorkCheckHandler,
                                     LessonHandler, MaterialManageHandler, ManageRightsHandler,
                                     HomeWorkManageHandler, LectorRegisterHandler)
from handlers.stream_handlers import StreamAuthHandler, StreamUpdateHandler, StreamTstHandler, StreamDoneHandler
from handlers.study_handlers import (StudyFindHandler, StudyLiveHandler, StudyManageHandler, StudyCourseHandler,
                                     StudyLessonHandler,
                                     StudyInviteHandler, StudyRegisterHandler, StudyHomeWorkHandler)
from handlers.media_handlers import MaterialHandler

import uimodules


class Application(tornado.web.Application):

    def __init__(self):

        handlers = [
            (r"/", MainHandler),
            (r"/ws/update/main/", WsUpdateMainHandler),

            (r"/about", AboutHandler),
            (r"/room", RoomHandler),

            (r"/stream", StreamTstHandler),
            (r"/stream/auth", StreamAuthHandler),
            (r"/stream/update", StreamUpdateHandler),
            (r"/stream/done", StreamDoneHandler),

            (r"/auth/login", LoginHandler),
            (r"/auth/logout", LogoutHandler),
            (r"/auth/register", RegisterHandler),

            (r"/teach", CoursesHandler),
            (r"/teach/rights", ManageRightsHandler),
            (r"/teach/register", LectorRegisterHandler),
            (r"/teach/create", CreateCourseHandler),
            (r"/teach/manage", ManageCourseHandler),
            (r"/teach/lesson", LessonHandler),
            (r"/teach/lesson/homework", HomeWorkManageHandler),
            (r"/teach/lesson/homework/check", HomeWorkCheckHandler),
            (r"/teach/lesson/material", MaterialManageHandler),

            (r"/study/live", StudyLiveHandler),
            (r"/study/find", StudyFindHandler),
            (r"/study/manage", StudyManageHandler),
            (r"/study/homework", StudyHomeWorkHandler),
            (r"/study/invite", StudyInviteHandler),
            (r"/study/register/(.*)", StudyRegisterHandler),
            (r"/study/course/(.*)", StudyCourseHandler),
            (r"/study/lesson/(.*)", StudyLessonHandler),

            (r"/media/material/(.*)", MaterialHandler),

            (r"/(.*)/(.*)/(.*)", AssetsLibHandler),
            (r"/css/(.*)", CssHandler),
        ]

        settings = {
            "static_path": sets.STATIC_PATH,
            "cookie_secret": sets.COOKIE_SECRET,
            "login_url": "/auth/login",
            "xsrf_cookies": True,
            'template_path': sets.TEMPLATE_PATH,
            'debug': sets.DEBUG,
            'ui_modules': uimodules,
        }

        tornado.web.Application.__init__(self, handlers, **settings)



if __name__ == "__main__":

    
    print('server on 0.0.0.0:8888 started.')
    app = Application()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

