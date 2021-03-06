from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from db.custom_types import Choice


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(length=30))
    password = Column(String(length=60))
    email = Column(String(length=60))

    _lesson_access = relationship('LessonAccess', back_populates='_user')
    _course_access = relationship('CourseAccess', back_populates='_user')

    _course = relationship('Course', back_populates='_owner')
    _course_member = relationship("CourseMembers", back_populates="_member")
    _course_invites = relationship("CourseInvites", back_populates="_member")
    _home_work_answer = relationship("HomeWorkAnswer", back_populates="_source")


class CourseAccess(Base):
    __tablename__ = 'course_access'

    BROWSE = 'Browse'
    MODERATE = 'Moderate'
    COURSE_LEVEL = {
        BROWSE: 'R',
        MODERATE: 'W',
    }

    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey('user.id'))
    course = Column(Integer, ForeignKey('course.id'))
    access = Column(Choice(COURSE_LEVEL))

    _user = relationship('User', back_populates='_course_access')
    _course = relationship('Course', back_populates='_course_access')


class LessonAccess(Base):
    __tablename__ = 'lesson_access'

    VIEW = 'View'
    TEACH = 'Teach'  # Include checking homework and setup grade!
    MODERATE = 'Moderate'
    LESSON_LEVEL = {
        TEACH: 'T',
        MODERATE: 'W',
        VIEW: 'R'
    }

    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey('user.id'))
    lesson = Column(Integer, ForeignKey('lesson.id'))
    access = Column(Choice(LESSON_LEVEL))

    _user = relationship('User', back_populates='_lesson_access')
    _lesson = relationship('Lesson', back_populates='_lesson_access')


class Course(Base):
    __tablename__ = 'course'

    OPEN = 'Open'
    CLOSED = 'Closed'
    PRIVATE = 'Private'
    COURSE_MODES = {
        OPEN: 'O',
        CLOSED: 'C',
        PRIVATE: 'P',
    }
    CREATED = 'Created'
    PUBLISHED = 'Published'
    LIVE = 'Live'
    INTERRUPTED = 'Interrupted'
    ENDED = 'Ended'
    COURSE_STATES = {
        CREATED: 'C',
        PUBLISHED: 'P',
        LIVE: 'L',
        INTERRUPTED: 'I',
        ENDED: 'E',
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(length=30))
    description = Column(Text)
    owner = Column(Integer, ForeignKey('user.id'))
    mode = Column(Choice(COURSE_MODES))
    state = Column(Choice(COURSE_STATES))
    invite_url = Column(String(length=36))  # for invites learners in private course
    invite_lector_url = Column(String(length=36))

    _owner = relationship("User", back_populates="_course")
    _course_access = relationship('CourseAccess', back_populates='_course', cascade="save-update, merge, delete")
    _lesson = relationship("Lesson", back_populates="_course", cascade="save-update, merge, delete")
    _course_member = relationship('CourseMembers', back_populates='_course', cascade="save-update, merge, delete")
    _course_invites = relationship("CourseInvites", back_populates="_course", cascade="save-update, merge, delete")


class Lesson(Base):
    __tablename__ = 'lesson'

    LIVE = 'Live'
    WAITING = 'Waiting'
    INTERRUPTED = 'Interrupted'
    ENDED = 'Ended'

    LESSON_STATE = {
        LIVE: 'L',
        WAITING: 'W',
        INTERRUPTED: 'I',
        ENDED: 'E',
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(length=30))
    description = Column(Text)
    start_time = Column(DateTime)
    duration = Column(Integer)
    state = Column(Choice(LESSON_STATE))
    course = Column(Integer, ForeignKey('course.id'))

    stream_key = Column(String(length=36))
    stream_pw  = Column(String(length=12))

    _lesson_access = relationship('LessonAccess', back_populates='_lesson', cascade="save-update, merge, delete")
    _course = relationship("Course", back_populates="_lesson")
    _lesson_material = relationship("LessonMaterial", back_populates="_lesson")
    _home_work = relationship("HomeWork", back_populates="_lesson")

    def start_time_in_format(self, format='%H:%M'):
        now = datetime.now()
        dt = self.start_time
        dt_s = dt.strftime(format)
        filled = False
        if now.year == dt.year and now.month == dt.month:
            if dt.day == now.day:
                dt_s = "today " + dt_s
                filled = True
            elif dt.day == now.day + 1:
                dt_s = "tomorrow " + dt_s
                filled = True
        if not filled:
            dt_s += " (" + dt.strftime("%Y-%m-%d") + ")"
        return dt_s


class CourseMembers(Base):
    __tablename__ = 'course_member'

    id = Column(Integer, primary_key=True)

    course = Column(Integer, ForeignKey('course.id'))
    member = Column(Integer, ForeignKey('user.id'))
    assign_type = Column(Choice(Course.COURSE_MODES))

    _course = relationship("Course", back_populates="_course_member")
    _member = relationship("User", back_populates="_course_member")


class CourseInvites(Base):
    __tablename__ = 'course_invites'

    TEACH = 'Teach'
    LEARN = 'Learn'

    INVITE_TYPES = {
        TEACH: 'T',
        LEARN: 'L',
    }
    id = Column(Integer, primary_key=True)
    course = Column(Integer, ForeignKey('course.id'))
    member = Column(Integer, ForeignKey('user.id'))
    action = Column(Choice(INVITE_TYPES))

    __table_args__ = UniqueConstraint('course', 'member', name='_course_course_uc'),  # must be tupple!

    _course = relationship("Course", back_populates="_course_invites")
    _member = relationship("User", back_populates="_course_invites")


class LessonMaterial(Base):
    __tablename__ = 'lesson_material'

    id = Column(Integer, primary_key=True)
    pretty_name = Column(String(length=255))
    real_name = Column(String(length=255))
    parent_dir = Column(String(length=10))
    lesson = Column(Integer, ForeignKey('lesson.id'))

    _lesson = relationship("Lesson", back_populates="_lesson_material")


class HomeWork(Base):
    __tablename__ = 'home_work'

    id = Column(Integer, primary_key=True)
    title = Column(String(length=200))
    description = Column(Text)
    lesson = Column(Integer, ForeignKey('lesson.id'))

    _lesson = relationship("Lesson", back_populates="_home_work")
    _home_work_answer = relationship("HomeWorkAnswer", back_populates="_home_work", cascade="save-update, merge, delete")


class HomeWorkAnswer(Base):
    __tablename__ = 'home_work_answer'

    id = Column(Integer, primary_key=True)
    description = Column(Text)
    home_work = Column(Integer, ForeignKey('home_work.id'))
    source = Column(Integer, ForeignKey('user.id'))
    grade = Column(Integer)  # in %

    _home_work = relationship("HomeWork", back_populates="_home_work_answer")
    _source = relationship("User", back_populates="_home_work_answer")