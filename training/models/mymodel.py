# -*- coding: utf-8

import hashlib
import datetime
import json
from dateutil import rrule


from sqlalchemy import (
    Column,
    Index,
    Integer,
    Boolean,
    String,
    Text,
    Enum,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import validates, relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Table
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from .meta import Base

class User(Base):
    __tablename__ = 'users'
    id = Column('id', Integer, primary_key=True)
    name = Column(String(200))
    login = Column(String(200))
    password = Column(Text)
    comments = Column(Text)
    is_admin = Column(Integer, default=0)
    is_author = Column(Integer, default=0)
    is_confirmed = Column(Integer, default=0)
    flags = Column(Integer, default=0)
    lastchanged = Column(DateTime, nullable=False, default=datetime.datetime.utcnow())
    
    @validates('login')
    def validate_login(self, key, address):
        assert '@' in address
        return address

    def __str__(self):
        return self.name

# добавить цену и продолжительность подписки
# цена - понятно,
# продолжительность - timedelta между start и end

class SubscrType(Base):
    __tablename__ = 'subscriptiontypes'
    id = Column('id', Integer, primary_key=True)
    subscrtype = Column(Enum("short", "onemonth", "sixmonths", "oneyear"))
    price = Column(Integer)
    numweeks = Column(Integer)
    comment = Column(Text)


class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column('id', Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    course_id = Column('course_id', Integer, ForeignKey('elements.id'))
    subscrtype_id = Column('subscrtype_id', Integer, ForeignKey('subscriptiontypes.id'))
    start = Column('start', DateTime)
    end = Column('end', DateTime)
    is_paused = Column(Integer, default=0)
    is_cancelled = Column(Integer, default=0)
    is_paid = Column(Integer, default=0)
    comments = Column(Text)
    flags = Column(Text)
    uname = relationship('User', backref='subscriptions')
    cname = relationship('CourseElement')
    lastchanged = Column(DateTime, nullable=False, default=datetime.datetime.utcnow())
    payment = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan", uselist=False)
    course = relationship("CourseElement")
    subscrtype = relationship("SubscrType")

    def __str__(self):
        return self.cname.name

    @hybrid_property
    def twolastweeks(self):
        now = datetime.datetime.utcnow()

        weeks = rrule.rrule(rrule.WEEKLY, dtstart=self.lastchanged, until=now)
        weekspassed = weeks.count() - 1
        #startday = (self.start - datetime.timedelta(days=self.start.weekday()))
        #today = (now - datetime.timedelta(days=now.weekday()))
        #dayspassed = (today - startday).days
        #weekspassed = dayspassed/7

        # TODO тест на длинных программах. Хотя вроде работает
        #print "^"*80
        #print weeks.count()
        #print weekspassed
        #print "^"*80


        if weekspassed == 0:
            return [self.course.children[weekspassed],]
        elif weekspassed < self.duration:
            return self.course.children[weekspassed-1:weekspassed+1][::-1]
        elif weekspassed == self.duration:
            return self.course.children[weekspassed-2:][::-1]
        else:
            return []

    @hybrid_property
    def is_finished(self):
        if self.end < datetime.datetime.utcnow():
            return 1
        else:
            return 0

    @hybrid_property
    def duration(self):
        # return numweeks = end - start
        mondayend = (self.end - datetime.timedelta(days=self.end.weekday()))
        mondaystart = (self.lastchanged - datetime.timedelta(days=self.lastchanged.weekday()))
        dur_weeks = (mondayend - mondaystart).days / 7
        return dur_weeks


class Article(Base):
    __tablename__ = 'articles'
    id = Column('id', Integer, primary_key=True)
    author_id = Column('author_id', Integer, ForeignKey('users.id'))
    header = Column(Text)
    headerimage = Column(Text)
    body = Column(Text)
    preview = Column(Text)
    is_published = Column(Integer, default=0)
    is_archived = Column(Integer, default=0)
    lastchanged = Column(DateTime, nullable=False, default=datetime.datetime.utcnow())
    author = relationship('User')

    @hybrid_property
    def objtype(self):
        return 'article'


# worklfow:
# add new course, description, preview, image etc.
# add weeks
# for every week add some workouts
# for every workout add excercise
# for every excercise fill data:
# name
# descr
# repeats
# sets
# rest
# perform for (time)
# 
# https://stackoverflow.com/questions/4896104/creating-a-tree-from-self-referential-tables-in-sqlalchemy
# http://docs.sqlalchemy.org/en/latest/orm/self_referential.html

class CourseElement(Base):
    __tablename__ = 'elements'
    id = Column('id', Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('elements.id'))
    # for course
    name = Column(String(200))
    author_id = Column('author_id', Integer, ForeignKey('users.id'))
    is_published = Column(Integer, default=0)
    is_archived = Column(Integer, default=0)
    lastchanged = Column(DateTime, nullable=False, default=datetime.datetime.utcnow())
    headerimage = Column(Text)
    preview =Column(Text)
    author = relationship('User')
    # for course elements:
    # for week and workout
    elemtype = Column(Enum('course', 'week', 'workout', 'round', 'exc'))
    weektype = Column(Enum('power', 'endurance', 'fingers', 'projecting', 'rest', 'test'))
    descr = Column(Text)
    timetotal = Column(String(200))
    # for excercise
    onerepis = Column(Text)
    griptype = Column(Text)
    numreps = Column(Integer)
    numsets = Column(Integer)
    resttime = Column(Text)
    finalrest = Column(Text)
    perftime = Column(String(200))
    comments = Column(Text)
    media = relationship("Media", backref="excercise")
    coursetype = Column(Enum("short", "long"))
    customorder = Column(String(200))

    children = relationship('CourseElement',
                            cascade="all",
                            backref=backref("parent", remote_side='CourseElement.id'),
                            order_by=[customorder, id]
                            )

    @hybrid_property
    def jsontree(self):
        outlist = []
        if self.parent is None:
            for ch in self.children:
                outlist.append(ch.jsondata)
        return json.dumps(outlist, indent=4)

    @hybrid_property
    def nextid(cls):
        return self.parent.children[(self.parent.children.index(self) + 1) % len(self.parent.children)].id

    @hybrid_property
    def previd(self):
        return self.parent.children[(self.parent.children.index(self) - 1) % len(self.parent.children)].id
        
    @hybrid_property
    def childindex(self):
        if self.parent is not None:
            for ind, el in enumerate(self.parent.children):
                if self.id == el.id:
                    return ind+1

    @hybrid_property
    def header(self):
        return self.name

    @hybrid_property
    def objtype(self):
        return self.elemtype

    @hybrid_property
    def trelemtype(self):
        objs = {'course':u'Курс','week':u'Неделя', 'workout':u'День', 'round':u'Раунд', 'exc':u'Упражнение'}
        return objs[self.elemtype]

    @hybrid_property
    def trweektype(self):
        objs = {'power':u'Сила', 'endurance':u'Выносливость', 'fingers':u'Сила пальцев', 'projecting':u'Трассы', 'rest':u"Отдых", 'test':u"Тест"}
        if self.weektype is not None:
            return objs[self.weektype]
        

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    def append(self, nodename):
        self.children[nodename] = CourseElement(nodename, parent=self)


class Media(Base):
    __tablename__ = 'media'
    id = Column('id', Integer, primary_key=True)
    excersise_id = Column('excercise_id', Integer, ForeignKey('elements.id'))
    mtype = Enum('img', 'vid')
    comments = Column(Text)
    url = Column(Text)

class Payment(Base):
    __tablename__ = 'payments'
    id = Column('id', Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    subscription_id = Column('subscription_id', Integer, ForeignKey('subscriptions.id'))
    subscription = relationship("Subscription", back_populates="payment")
    date = Column('date', DateTime)
    subscr = relationship('Subscription')
    status = Column(Enum('new', 'failed', 'confirmed', 'pending'))
    comments = Column(Text)
    descr = Column(Text)

    def __str__(self):
        transl = {"new": u"неоплачено",
                  "failed": u"неудачный",
                  "confirmed": u"оплачено",
                  "pending": u"ожидает подтверждения"
                  }
        return u"%s, %s, %s &#8381;, %s" % (self.date, self.descr, self.subscription.subscrtype.price, transl[self.status])
