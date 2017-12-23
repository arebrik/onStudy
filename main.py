# coding: utf-8
from os.path import join

import tornado.ioloop
import tornado.web

from settings import sets

from handlers.MainHandler import MainHandler, RoomHandler, AboutHandler
from handlers.auth import LogoutHandler, LoginHandler, RegisterHandler
from handlers.static_handlers import CssHandler, AssetsLibHandler


if __name__ == "__main__" and sets.DEBUG:
    from subprocess import call
    import sys

    call(sys.executable + " -m pip install -r requirements.txt", shell=True)
    call(sys.executable + " " + join("scripts", "install.py"), shell=True)
    call(sys.executable + " " + join("scripts", "init_db.py"), shell=True)



class Application(tornado.web.Application):

    def __init__(self):

        handlers = [
            (r"/", MainHandler),
            (r"/about", AboutHandler),
            (r"/room", RoomHandler),
            (r"/auth/login", LoginHandler),
            (r"/auth/logout", LogoutHandler),
            (r"/auth/register", RegisterHandler),
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
        }

        tornado.web.Application.__init__(self, handlers, **settings)



if __name__ == "__main__":
    app = Application()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
