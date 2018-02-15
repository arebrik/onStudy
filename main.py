# coding: utf-8
from os.path import join

from settings import sets


if __name__ == "__main__" and sets.DEBUG:
    print('[ INIT ]')
    
    from subprocess import call, DEVNULL, check_output
    import sys
    from datetime import datetime

    init_start = datetime.now()

    recom = lambda com: com if sys.platform.startswith("win") else ' '.join(com)

    _text = check_output(recom([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]),
                    shell=True)
    print('[ INIT ] 1: ', datetime.now() - init_start)

    if _text.count(b'already satisfied') != 6 or (b'Successfully installed' in _text and b'fail' not in _text.lower()):
        raise Exception('Wrong requirements:\n\t' + _text.decode('utf-8'))

    call(recom([sys.executable, join("scripts", "install.py")]), shell=True)

    print('[ INIT ] 2: ', datetime.now() - init_start)

    call(recom([sys.executable, join("scripts", "init_db.py"), "dont_remove"]), shell=True)

    print('[ INIT ] fin into: ', datetime.now() - init_start)


import tornado.ioloop
import tornado.web

from handlers.MainHandler import MainHandler, RoomHandler, AboutHandler
from handlers.auth import LogoutHandler, LoginHandler, RegisterHandler
from handlers.static_handlers import CssHandler, AssetsLibHandler
from handlers.course_manager import CreateCourseHandler, ManageCourseHandler, CourseHandler, LessonHandler
from handlers.stream_handlers import StreamAuthHandler, StreamUpdateHandler, StreamTstHandler


class Application(tornado.web.Application):

    def __init__(self):

        handlers = [
            (r"/", MainHandler),
            (r"/about", AboutHandler),
            (r"/room", RoomHandler),

            (r"/stream", StreamTstHandler),
            (r"/stream/auth", StreamAuthHandler),
            (r"/stream/update", StreamUpdateHandler),

            (r"/auth/login", LoginHandler),
            (r"/auth/logout", LogoutHandler),
            (r"/auth/register", RegisterHandler),
            (r"/(.*)/(.*)/(.*)", AssetsLibHandler),
            (r"/css/(.*)", CssHandler),

            (r"/course", CourseHandler),
            (r"/course/create", CreateCourseHandler),
            (r"/course/manage", ManageCourseHandler),
            (r"/course/lesson", LessonHandler),
        ]

        settings = {
            "static_path": sets.STATIC_PATH,
            "cookie_secret": sets.COOKIE_SECRET,
            "login_url": "/auth/login",
            "xsrf_cookies": True,
            'template_path': sets.TEMPLATE_PATH,
            'debug': sets.DEBUG,
        }

        tornado.web.Application.__init__(self, handlers, **settings)



if __name__ == "__main__":
    print('server on 0.0.0.0:8888 started.')
    app = Application()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

