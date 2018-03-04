from datetime import timedelta, datetime
from uuid import uuid4

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import or_

from db.models import CourseMembers, Course, User, Lesson, CourseInvites
from db.DBBridge import DBBridge
from settings import sets

from logging import getLogger
log = getLogger(__name__)


class DbHandlerBase:

    def __init__(self, dbb: DBBridge):
        self.dbb = dbb


class UserHandler(DbHandlerBase):

    @staticmethod
    @DBBridge.query_db
    def get(session, username: str):
        user = session.query(User).filter(User.name == username).one_or_none()
        return user

    @staticmethod
    @DBBridge.query_db
    def get_by_email(session, email):
        return session.query(User).filter(User.email == email).one_or_none()

    @staticmethod
    @DBBridge.modife_db
    def create(session, username, password, email):
        # TODO: check if username/email already exist
        user = User(name=username, password=password, email=email)
        session.add(user)


class CourseHandler(DbHandlerBase):

    @staticmethod
    @DBBridge.query_db
    def get_by_owner(session, course_name, username):
        user = UserHandler.get(username)
        lessons = []
        members = []
        course = session.query(Course).filter(Course.name == course_name, Course.owner == user.id).one()
        for l in course._lesson:
            lessons.append(l)
        for member in course._course_member:
            members.append(member._member.name)
        return course, lessons, members

    @staticmethod
    @DBBridge.query_db
    def get(session, course_name):
        course = session.query(Course).filter(Course.name == course_name).one_or_none()
        return course

    @staticmethod
    @DBBridge.query_db
    def get_by_stream_key(session, key):
        return session.query(Course).filter(Course.stream_key == key).one_or_none()

    @staticmethod
    @DBBridge.query_db
    def get_open_course_live_lesson(session):
        lives = []
        try:
            courses = session.query(Course).filter(
                Course.mode == Course.OPEN,
                Course.state == Course.LIVE,
            )
            for c in courses:
                for lesson in c._lesson:
                    if lesson.state == Lesson.LIVE or lesson.state == Lesson.INTERRUPTED:
                        lives.append(lesson)
        except NoResultFound:
            print('No LIVE course')
            pass
        return lives

    @staticmethod
    @DBBridge.query_db
    def get_all_course(session, username):
        user = UserHandler.get(username)
        open_courses = []
        closed_courses = []
        try:
            courses = session.query(Course).filter(
                or_(Course.state == Course.LIVE, Course.state == Course.PUBLISHED),
                or_(Course.mode == Course.OPEN, Course.mode == Course.CLOSED),
            )
            for c in courses:
                already_member = False
                for member in c._course_member:
                    if member.member == user.id:
                        already_member = True
                if already_member:
                    continue
                if c.mode == Course.OPEN:
                    open_courses.append(c)
                else:
                    closed_courses.append(c)
        except NoResultFound:
            print('NO open or closed courses on server ;(')
        return open_courses, closed_courses

    @staticmethod
    @DBBridge.query_db
    def get_all_by_owner(session, username):
        user = UserHandler.get(username)
        try:
            courses = session.query(Course).filter(Course.owner == user.id)
        except NoResultFound:
            courses = None
        return courses

    @staticmethod
    @DBBridge.modife_db
    def create(session, username, course_name, course_descr, mode):
        user = UserHandler.get(username)

        c = None
        if not CourseHandler.get(course_name):
            c = Course(
                name=course_name,
                description=course_descr,
                owner= user.id,
                mode=mode,
                state=Course.CREATED,
            )
            session.add(c)
        return c

    @staticmethod
    @DBBridge.modife_db
    def associate_with_course(session, username, course_name):
        # TODO: verify if username already member of course_name
        # TODO: verify if username CAN be a member of course_name
        user = UserHandler.get(username)
        course = CourseHandler.get(course_name)
        if not CourseMembersHandler.get_member_by_course(course.id, user.id):
            cm = CourseMembers(
                course=course.id,
                member=user.id,
                assign_type=course.mode,
            )
            log.info('Associate user "{}" with course "{}"'.format(username, course_name))
            session.add(cm)
            return cm

    @staticmethod
    @DBBridge.modife_db
    def change_state(session, username, course_name, state):
        course = CourseHandler.get(course_name)
        course.state = state


class LessonHandler(DbHandlerBase):

    @staticmethod
    @DBBridge.query_db
    def get_by_keys(session, stream_key, stream_pw):
        return session.query(Lesson).filter(
            Lesson.stream_key == stream_key, Lesson.stream_pw == stream_pw
        ).one_or_none()

    @staticmethod
    @DBBridge.modife_db
    def activate_lesson(session, stream_key, stream_pw):
        lesson = LessonHandler.get_by_keys(stream_key, stream_pw)
        if lesson and lesson.state != lesson.ENDED:
            accept_start = lesson.start_time - timedelta(minutes=sets.STREAM_WINDOW)
            accept_end = lesson.start_time + timedelta(minutes=lesson.duration) + timedelta(minutes=sets.STREAM_WINDOW)
            if accept_start < datetime.now() < accept_end:
                if lesson.state == Lesson.WAITING or lesson.state == Lesson.INTERRUPTED:
                    lesson.state = Lesson.LIVE
                    log.debug('change lesson "{}" state from "{}" to "Live"'.format(lesson.name, lesson.state))
                    if lesson._course.state != Course.LIVE:
                        lesson._course.state = Course.LIVE
                        log.debug('Change course "{}" state to live'.format(lesson._course.name))
            else:
                lesson = None
        return lesson

    @staticmethod
    @DBBridge.modife_db
    def stop_lesson(session, stream_key, stream_pw):
        lesson = LessonHandler.get_by_keys(stream_key, stream_pw)
        if lesson.state != Lesson.LIVE:
            # this can`t be possible on normal request
            return
        lesson.state = Lesson.INTERRUPTED

    @staticmethod
    @DBBridge.modife_db
    def create_lesson(session, username, course_name, l_name, l_descr, start_time, dur):
        # TODO: check if 'l_name' not already exist in lessons 'course_name'
        # TODO: check start_time (not cross with other lessons and in future)
        # TODO: check dur (must be non zero posivite value)
        course, _, _ = CourseHandler.get_by_owner(course_name, username)
        l = Lesson(
            name=l_name,
            description=l_descr,
            start_time=start_time,
            duration=dur,
            state=Lesson.WAITING,
            course=course.id,
            stream_key=str(uuid4()),
            stream_pw=str(uuid4()).split('-')[-1]  # last string after '-' in ******-****-****-****-******
        )
        session.add(l)
        return l

    @staticmethod
    @DBBridge.modife_db
    def delete_lesson(session, username, course_name, lesson_name):
        course, lessons, _ = CourseHandler.get_by_owner(course_name, username)
        for l in lessons:
            if l.name == lesson_name:
                session.delete(l)
                return l


class CourseMembersHandler(DbHandlerBase):

    @staticmethod
    @DBBridge.query_db
    def get_member_by_course(session, course_id, user_id):
        return session.query(CourseMembers).filter(
            CourseMembers.course == course_id, CourseMembers.member == user_id
        ).one_or_none()

    @staticmethod
    @DBBridge.query_db
    def get_all_study_course(session, username):
        user = UserHandler.get(username)
        user_in = session.query(CourseMembers).filter(CourseMembers.member == user.id)
        return user_in


class CourseInvitesHandler(DbHandlerBase):

    @staticmethod
    @DBBridge.query_db
    def get_user_invites(session, username):
        user = UserHandler.get(username)
        invites = session.query(CourseInvites).filter(CourseInvites.member == user.id)
        return invites

    @staticmethod
    @DBBridge.modife_db
    def invite_on_decline(session, course_name, invited_user):
        user_course = CourseInvitesHandler.get_user_invites(invited_user)
        for c in user_course:
            if c._course.name == course_name:
                session.delete(c)
                return c
        log.warning('No association for user "{}" and course "{}" in CourseInvites'.format(invited_user, course_name))

    @staticmethod
    @DBBridge.modife_db
    def invite_on_accept(session, course_name, invited_user):
        CourseInvitesHandler.invite_on_decline(course_name, invited_user)
        CourseHandler.associate_with_course(invited_user, course_name)

    @staticmethod
    @DBBridge.modife_db
    def create_invite(session, course_name, owner, user_to_invite):
        # TODO: check if user_to_invite already invited to this course
        course = CourseHandler.get(course_name)
        if course._owner.name != owner:
            log.debug('Bad Request')
            return
        user = UserHandler.get(owner)
        if not user:
            log.debug('User with that name doesn`t exist!')
        i = CourseInvites(course=course.id, member=user.id)
        session.add(i)
        return i

