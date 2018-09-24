# -*- coding: utf-8

import hashlib
import smtplib
import datetime
import transaction
import json
from functools import wraps
import email.mime.multipart
from email.mime.text import MIMEText
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.security import (
    authenticated_userid,
    forget,
    remember
)

from pyramid.events import subscriber
from pyramid.events import BeforeRender

from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPFound,
    HTTPNotFound,
    HTTPSeeOther
)

from pyramid.i18n import (
    TranslationStringFactory,
    get_localizer,
    get_locale_name
)

from sqlalchemy.exc import DBAPIError
from sqlalchemy.sql import and_, or_, not_

from ..models import User, CourseElement, Media, Subscription, Payment, Article, SubscrType

#auth_decorator
#def login_required(func):
#    @wraps(func)
#    def new_func(request):
#        if(request.cookies.get('user')): 
#            return func(request)
#
#        else:
#            return Response('not authirised')
#    return new_func


@subscriber(BeforeRender)
def add_global(event):
    # заполняем глобальные переменные, чтобы 
    # не передавать их в каждый шаблон
    request = event.get('request')
    cfg = request.registry.settings
    mailto = cfg.get('email')
    phone = cfg.get('tel')
    whatsappphone = cfg.get('whatsapp')
    event['phone'] = phone
    event['email'] = mailto
    event['whatsappphone'] = whatsappphone
    courses = request.dbsession.query(CourseElement).filter(CourseElement.parent_id == None).filter(CourseElement.is_published == 1).filter(not_(CourseElement.is_archived)).order_by(CourseElement.name).all()
    authors = request.dbsession.query(User).filter(or_(User.is_author == 1, User.is_admin==1)).order_by(User.is_admin.desc()).all()
    event['authors'] = authors
    event['courses'] = courses
    if authenticated_userid(request):
        user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
        event['authuser'] = user


@view_config(route_name='modifycourse', renderer='../templates/coursemodifytemplate.jinja2')
def modify(request):
    if not authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('home'))
    user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
    if not user.is_author:
        return HTTPSeeOther(location=request.route_url('home'))
    tpl = {}
    cid = int(request.matchdict['courseid'])
    tomodify = request.dbsession.query(CourseElement).filter(CourseElement.id==cid).first()
    #allweeks = request.dbsession.query(CourseElement).filter(CourseElement.elemtype=='week').all()
    tpl.update({'course':tomodify})#, 'allweeks':allweeks})
    return tpl

@view_config(route_name='courseaction', renderer='../templates/courseaction.jinja2')
def courseaction(request):
    """
    add/delete/modify
    ?week, wkt, exc
    """

    actions = {'new': u"Добавление", 'edit': u"Правка", 'delete': u"Удаление"}
    objs = {'week':u'недели', 'workout':u'дня', 'round':u'группы', 'excercise':u'упражнения'}

    if not authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('home'))

    if request.POST:
        try:
            csrf = request.POST.get('csrf')
            action = request.POST.get('action')
            what = request.POST.get('objtype')
            pid = int(request.POST.get('pid'))
            
        except:
            raise HTTPNotFound()

        if csrf == request.session.get_csrf_token():
            if action == 'new':
                if what == 'week':
                    weekdescr = request.POST.get('weekdescr')
                    weektype = request.POST.get('weektype')
                    elemtype = what
                    corder = request.POST.get('customorder')
                    newelem = CourseElement(parent_id=pid,
                                            elemtype=elemtype,
                                            weektype=weektype,
                                            descr=weekdescr,
                                            customorder=corder
                                            )
                    request.dbsession.add(newelem)
                    request.session.flash({
                            'class' : 'success',
                            'text'  : u'Данные сохранены'
                            })
                    if 'submitmore' in request.POST.keys():
                        ordid = request.POST.get('ordid')
                        return HTTPSeeOther(location=request.route_url('courseaction', courseid=pid, args=('new', what, pid, ordid)))
                    return HTTPSeeOther(location=request.route_url('modifycourse', courseid=pid))

                elif what == 'workout':
                    elem = request.dbsession.query(CourseElement).filter(CourseElement.id==pid).first()
                    wktdescr = request.POST.get('wktdescr')
                    wkttype = request.POST.get('wkttype')
                    elemtype = what
                    totaltime = request.POST.get('wkttotaltime')
                    corder = request.POST.get('customorder')
                    newelem = CourseElement(parent_id=pid,
                                            elemtype='workout',
                                            weektype=wkttype,
                                            descr=wktdescr,
                                            timetotal = totaltime, 
                                            customorder = corder
                                            )
                    request.dbsession.add(newelem)
                    request.session.flash({
                            'class' : 'success',
                            'text'  : u'Данные сохранены'
                            })
                    if 'submitmore' in request.POST.keys():
                        ordid = request.POST.get('ordid')
                        return HTTPSeeOther(location=request.route_url('courseaction', courseid=elem.parent.id, args=('new', what, pid, ordid)))
                    
                    return HTTPSeeOther(location=request.route_url('modifycourse', courseid=elem.parent.id))

                elif what == 'round':
                    elem = request.dbsession.query(CourseElement).filter(CourseElement.id==pid).first()
                    roundname = request.POST.get('roundname')
                    rounddescr = request.POST.get('rounddescr')
                    corder = request.POST.get('customorder')
                    newelem = CourseElement(parent_id=pid,
                                            elemtype='round',
                                            name=roundname,
                                            descr=rounddescr,
                                            customorder=corder
                                            )
                    request.dbsession.add(newelem)
                    request.session.flash({
                            'class' : 'success',
                            'text'  : u'Данные сохранены'
                            })
                    if 'submitmore' in request.POST.keys():
                        ordid = request.POST.get('ordid')
                        return HTTPSeeOther(location=request.route_url('courseaction', courseid=elem.parent.parent.id, args=('new', what, pid, ordid)))
                    
                    return HTTPSeeOther(location=request.route_url('modifycourse', courseid=elem.parent.parent.id))


                elif what == 'excercise':
                    elem = request.dbsession.query(CourseElement).filter(CourseElement.id==pid).first()
                    excdescr = request.POST.get('excdescr')
                    excname = request.POST.get('excname')
                    onerepis = request.POST.get('onerepis')
                    numsets = request.POST.get('numsets')
                    numreps = request.POST.get('numreps')
                    griptype = request.POST.get('griptype')
                    perftime = request.POST.get('perftime')
                    resttime = request.POST.get('resttime')
                    finalrest = request.POST.get('finalrest')
                    corder = request.POST.get('customorder')
                    newelem = CourseElement(parent_id=pid,
                                            elemtype='exc',
                                            name=excname,
                                            descr=excdescr,
                                            onerepis=onerepis,
                                            numsets=numsets,
                                            numreps=numreps,
                                            griptype=griptype,
                                            perftime=perftime,
                                            resttime=resttime,
                                            finalrest=finalrest,
                                            customorder=corder
                                            )
                    request.dbsession.add(newelem)
                    request.session.flash({
                            'class' : 'success',
                            'text'  : u'Данные сохранены'
                            })
                    if 'submitmore' in request.POST.keys():
                        ordid = request.POST.get('ordid')
                        return HTTPSeeOther(location=request.route_url('courseaction', courseid=elem.parent.parent.parent.id, args=('new', what, pid, ordid)))

                    return HTTPSeeOther(location=request.route_url('modifycourse', courseid=elem.parent.parent.parent.id))


            elif action == 'edit':
                objid = int(request.POST.get('objid'))
                editelem = request.dbsession.query(CourseElement).filter(CourseElement.id==objid).first()
                if what == 'week':
                    weekdescr = request.POST.get('weekdescr')
                    weektype = request.POST.get('weektype')
                    objtype = request.POST.get('objtype')
                    corder = request.POST.get('customorder')
                    if corder == '':
                        corder = None
                    editelem.weektype = weektype
                    editelem.elemtype = objtype
                    editelem.descr = weekdescr
                    editelem.customorder = corder
                    request.dbsession.add(editelem)
                    request.session.flash({
                            'class' : 'success',
                            'text'  : u'Данные сохранены'
                            })

                    return HTTPSeeOther(location=request.route_url('modifycourse', courseid=editelem.parent.id))

                elif what == "workout":
                    wktdescr = request.POST.get('wktdescr')
                    wkttype = request.POST.get('wkttype')
                    wkttotaltime = request.POST.get('wkttotaltime')
                    corder = request.POST.get('customorder')
                    if corder == '':
                        corder = None

                    editelem.descr = wktdescr
                    editelem.weektype = wkttype
                    editelem.timetotal = wkttotaltime
                    editelem.customorder = corder
                    request.dbsession.add(editelem)
                    request.session.flash({
                            'class' : 'success',
                            'text'  : u'Данные сохранены'
                            })

                    return HTTPSeeOther(location=request.route_url('modifycourse', courseid=editelem.parent.parent.id))
                    
                elif what == "round":
                    rnddescr = request.POST.get('rounddescr')
                    rndname = request.POST.get('roundname')
                    corder = request.POST.get('customorder')
                    if corder == '':
                        corder = None

                    editelem.name = rndname
                    editelem.descr = rnddescr
                    editelem.customorder = corder
                    request.dbsession.add(editelem)
                    request.session.flash({
                            'class' : 'success',
                            'text'  : u'Данные сохранены'
                            })

                    return HTTPSeeOther(location=request.route_url('modifycourse', courseid=editelem.parent.parent.parent.id))
                
                elif what == "excercise":
                    excdescr = request.POST.get('excdescr')
                    excname = request.POST.get('excname')
                    onerepis = request.POST.get('onerepis')
                    numsets = request.POST.get('numsets')
                    numreps = request.POST.get('numreps')
                    griptype = request.POST.get('griptype')
                    perftime = request.POST.get('perftime')
                    resttime = request.POST.get('resttime')
                    finalrest = request.POST.get('finalrest')
                    corder = request.POST.get('customorder')
                    if corder == '':
                        corder = None

                    editelem.name = excname
                    editelem.descr = excdescr
                    editelem.onerepis = onerepis
                    editelem.numsets = numsets
                    editelem.numreps = numreps
                    editelem.griptype = griptype
                    editelem.perftime = perftime
                    editelem.resttime = resttime
                    editelem.finalrest = finalrest
                    editelem.customorder = corder
                    request.dbsession.add(editelem)
                    request.session.flash({
                            'class' : 'success',
                            'text'  : u'Данные сохранены'
                            })
                    
                    return HTTPSeeOther(location=request.route_url('modifycourse', courseid=editelem.parent.parent.parent.parent.id))
                else:
                    raise HTTPNotFound()
            else:
                raise HTTPNotFound()
    else:
        parentid = request.matchdict['courseid']
        action = request.matchdict['args'][0]
        what = request.matchdict['args'][1]
        if action == 'new':
            if what == 'week':
                parentcourse = request.dbsession.query(CourseElement).filter(CourseElement.id==parentid).first()
                tpl = {'parent': parentcourse, "actions":actions, "act":action, "objs":objs, "what":what}
                return tpl
            elif what == 'workout':
                try:
                    whatid = int(request.matchdict['args'][2])
                    orderid = int(request.matchdict['args'][3])
                except:
                    raise HTTPNotFound()

                parentcourse = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                tpl = {'parent': parentcourse, "actions":actions, "act":action, "objs":objs, "what":what, "ordid":orderid}
                return tpl

            elif what == 'round':
                try:
                    whatid = int(request.matchdict['args'][2])
                    orderid = int(request.matchdict['args'][3])
                except:
                    raise HTTPNotFound()

                parentcourse = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                tpl = {'parent': parentcourse, "actions":actions, "act":action, "objs":objs, "what":what, "ordid":orderid}
                return tpl
            
            elif what == 'excercise':
                try:
                    whatid = int(request.matchdict['args'][2])
                    orderid = int(request.matchdict['args'][3])
                except:
                    raise HTTPNotFound()
                
                parentcourse = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                tpl = {'parent': parentcourse, "actions":actions, "act":action, "objs":objs, "what":what, "ordid":orderid}
                return tpl
            else:
                raise HTTPNotFound()

        elif action == 'edit':
            
            parentcourse = request.dbsession.query(CourseElement).filter(CourseElement.id==parentid).first()
            if what == 'week':
                try:
                    whatid = int(request.matchdict['args'][2])
                except:
                    raise HTTPNotFound()
                obj = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                tpl = {'parent': parentcourse, "actions":actions, "act":action, "objs":objs, "what":what, "obj":obj}
                return tpl
            elif what == "workout":
                try:
                    whatid = int(request.matchdict['args'][2])
                    orderid = int(request.matchdict['args'][3])

                except:
                    raise HTTPNotFound()
                parentcourse = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                obj = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                tpl = {'parent': parentcourse, "actions":actions, "act":action, "objs":objs, "what":what, "obj":obj, "ordid":orderid}
                return tpl

            elif what == "round":
                try:
                    whatid = int(request.matchdict['args'][2])
                    orderid = int(request.matchdict['args'][3])

                except:
                    raise HTTPNotFound()
                parentcourse = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                obj = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                tpl = {'parent': parentcourse, "actions":actions, "act":action, "objs":objs, "what":what, "obj":obj, "ordid":orderid}
                return tpl
            elif what == "excercise":
                try:
                    whatid = int(request.matchdict['args'][2])
                    orderid = int(request.matchdict['args'][3])
                    
                except:
                    raise HTTPNotFound()
                parentcourse = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                obj = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
                tpl = {'parent': parentcourse, "actions":actions, "act":action, "objs":objs, "what":what, "obj":obj, "ordid":orderid}
                return tpl

        elif action == 'delete':
            whatid = int(request.matchdict['args'][2])
            todelete = request.dbsession.query(CourseElement).filter(CourseElement.id==whatid).first()
            request.dbsession.delete(todelete)
            request.session.flash({
                    'class' : 'success',
                    'text'  : u'Данные удалены'
                    })
            return HTTPSeeOther(location=request.route_url('modifycourse', courseid=parentid))
        else:
            raise HTTPNotFound()

@view_config(route_name='showone', renderer='../templates/articletemplate.jinja2')
def showoneview(request):
    tpl = {}
    objid = request.matchdict['id']
    what = request.matchdict['what']

    if what == 'article':
        q = request.dbsession.query(Article)
        obj = Article
    if what == 'course':
        q = request.dbsession.query(CourseElement).filter(CourseElement.parent_id == None)
        obj = CourseElement
    
    if not authenticated_userid(request):
        res = q.filter(obj.id==objid).filter(obj.is_published==1).filter(not_(obj.is_archived)).first()
    else:
        user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
        res = q.filter(obj.id==objid).filter(obj.is_published==1).filter(not_(obj.is_archived)).first()

        if user.is_author:
            res = q.filter(obj.id==objid).filter(not_(obj.is_archived)).first()
        if user.is_admin:
            res = q.filter(obj.id==objid).first()

    if res is None:
        raise HTTPNotFound()

    tpl.update({'obj':res})
    

    return tpl


@view_config(route_name='showall', renderer='../templates/articlestemplate.jinja2')
def showallview(request):
    tpl = {}
    what = request.matchdict['what']
    if what == 'articles':
        obj = Article
        q = request.dbsession.query(Article)

    if what == 'courses':
        obj = CourseElement
        q = request.dbsession.query(CourseElement).filter(CourseElement.parent_id == None)

    if not authenticated_userid(request):
        res = q.filter(obj.is_published==1).filter(not_(obj.is_archived))
    else:
        user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
        res = q.filter(obj.is_published==1).filter(not_(obj.is_archived))
        if user.is_author:
            res = q.filter(not_(obj.is_archived))
        if user.is_admin:
            res = q

    if what == 'courses':
        res = res.order_by(obj.name, obj.customorder).all()

    if what == 'articles':
        res = res.all()

    tpl.update({'obj':res})
    return tpl


@view_config(route_name='new', renderer='../templates/newarticlestemplate.jinja2')
def newview(request):
    if not authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('home'))

    user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
    if not user.is_author:
        return HTTPSeeOther(location=request.route_url('articles'))
    
    what = request.matchdict['what']
    tpl = {'what':what}

    if request.POST:
        if what == 'article':
            newobj = Article()
        elif what == 'course':
            newobj = CourseElement()
            
        csrf = request.POST.get('csrf', '')
        if csrf == request.session.get_csrf_token():
            newobj.author_id = user.id
            newobj.headerimage = request.POST.get('headimg')
          
            if user.is_admin:
                if 'published' in request.POST.keys():
                    newobj.is_published = 1
                else:
                    newobj.is_published = 0
                if 'archived' in request.POST.keys():
                    newobj.is_archived = 1
                else:
                    newobj.is_archived = 0

            if what == 'course':
                newobj.name = request.POST.get('head')
                newobj.coursetype = request.POST.get('long', 'short')
                newobj.elemtype = what
            elif what == 'article':
                 newobj.header = request.POST.get('head')

            newobj.preview = request.POST.get('preview')
            if what == 'article':
                newobj.body = request.POST.get('newpost')
            request.dbsession.add(newobj)
            request.session.flash({
                    'class' : 'success',
                    'text'  : u'Данные сохранены'
                    })
            return HTTPSeeOther(location=request.route_url('showall', what=what+'s'))
        else:
            request.session.flash({
                    'class' : 'warning',
                    'text'  : u'Что-то пошло не так, данные не сохранились'
                    })
            
            return HTTPSeeOther(location=request.route_url('new', what=what))
    
    return tpl

@view_config(route_name='edit', renderer='../templates/newarticlestemplate.jinja2')
def editview(request):
    if not authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('home'))

    user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
    what = request.matchdict['what']
    objid = request.matchdict['id']

    if not user.is_author:
        return HTTPSeeOther(location=request.route_url('showone', what=what, id=objid))

    tpl = {}
    if what == 'article':
        obj = Article
    if what == 'course':
        obj = CourseElement

    res = request.dbsession.query(obj).filter(obj.id == objid).first()        
    ## TODO добавить обработку правки и удаления юзеров
    if request.POST:
        
        csrf = request.POST.get('csrf', '')
        if csrf == request.session.get_csrf_token():
            if res.author_id == user.id:
                res.author_id = user.id
            res.headerimage = request.POST.get('headimg')
            if what == 'course':
                res.name = request.POST.get('head')
                print "*"*80
                print request.POST
                print "*"*80
                if request.POST.has_key('long'):
                    res.coursetype = 'long'
                else:
                    res.coursetype = 'short'

                res.elemtype = what
            else:
                res.header = request.POST.get('head')

            res.preview = request.POST.get('preview')

            if user.is_admin:
                if 'published' in request.POST.keys():
                    res.is_published = 1
                else:
                    res.is_published = 0
                if 'archived' in request.POST.keys():
                    res.is_archived = 1
                else:
                    res.is_archived = 0
            if request.POST.has_key('newpost'):
                res.body = request.POST.get('newpost')
            res.lastchanged = datetime.datetime.utcnow()
            request.dbsession.add(res)
            request.session.flash({
                    'class' : 'success',
                    'text'  : u'Изменения сохранены'
                    })
            return HTTPSeeOther(location=request.route_url('showone', what=what, id=objid))
        else:
            request.session.flash({
                    'class' : 'warning',
                    'text'  : u'Что-то пошло не так, не сохранено'
                    })
            
            return HTTPSeeOther(location=request.route_url('edit', what=what, id=objid))

    tpl.update({'obj':res})
    return tpl

@view_config(route_name='delete')
def deleteview(request):
    """
    the one to delete everything!
    """
    if not authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('home'))
    what = request.matchdict['what']
    objid = int(request.matchdict['id'])

    user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
    
    if what == 'payment':
        obj = Payment
        payment = request.dbsession.query(obj).filter(obj.id == objid).filter(obj.user_id == user.id).first()
        if payment is not None:
            subscr = payment.subscription
            request.dbsession.delete(payment)
            request.dbsession.delete(subscr)
            request.session.flash({
                    'class' : 'success',
                    'text'  : u'Платёж отменен'
                    })
    
            return HTTPSeeOther(location=request.route_url('settings'))

    if not user.is_author:
        return HTTPSeeOther(location=request.route_url('articles'))


    if what == 'article':
        obj = Article
    if what == 'course':
        obj = CourseElement

    todelete = request.dbsession.query(obj).filter(obj.id == objid).first()
    todelete.is_archived = 1
    todelete.is_published = 0
    request.dbsession.add(todelete)
    request.session.flash({
            'class' : 'success',
            'text'  : u'Данные отправлены в архив'
            })
    
    return HTTPSeeOther(location=request.route_url('showall', what=what+'s'))


@view_config(route_name='logout')
def logoutview(request):
    if authenticated_userid(request):
        headers = forget(request)
        return HTTPSeeOther(location=request.route_url('home'), headers=headers)
    return HTTPSeeOther(location=request.route_url('login'))

@view_config(route_name='about', renderer='../templates/abouttemplate.jinja2')
def aboutview(request):
    cfg = request.registry.settings
    tpl = {}
    return tpl        
    
@view_config(route_name='login', renderer='../templates/logintemplate.jinja2')
def loginview(request):
    cfg = request.registry.settings
    salt = cfg.get('salt')
    tpl = {}

    redirectto = request.session.get('redirectto', None)
    
    if authenticated_userid(request):
        if redirectto:
            return HTTPSeeOther(location=request.root+redirectto)
        return HTTPSeeOther(location=request.route_url('home'))

    if 'fname' in request.POST:
        fname = request.POST.get('fname', '')
        csrf = request.POST.get('csrf', '')
        login = request.POST.get('login', '')
        password = request.POST.get('password', '')

        if (csrf == request.session.get_csrf_token()) and login:
            if fname == 'login':
                q = request.dbsession.query(User).filter(User.login == login)
                if q.count() == 0:
                    request.session.flash({
                            'class' : 'info',
                            'text'  : u'Попробуйте зарегистрироваться и попробовать войти снова'
                            })
                    return HTTPSeeOther(location=request.route_url('login'))

                for user in q:
                    formpassword = hashlib.md5(salt+password.encode('utf-8')).hexdigest()

                    if user.password == formpassword:
                        headers = remember(request, login)
                        request.response.headerlist.extend(headers)
                        if redirectto:
                            del request.session['redirectto']
                            return HTTPSeeOther(location=request.host_url+redirectto, headers=headers)

                        return HTTPFound(request.route_url('home'), headers=headers)

                    request.session.flash({
                            'class' : 'warning',
                            'text'  : u'Неправильный пароль, простите'
                            })
                    return HTTPSeeOther(location=request.route_url('login'))

            elif fname == 'signup':
                # проверяем не занят ли логин
                q = request.dbsession.query(User).filter(User.login == login)
                if q.count() > 0:
                    request.session.flash({
                            'class' : 'info',
                            'text'  : u'Похоже, что такой адрес уже использован для регистрации. Вы точно еще не регистрировались?'
                            })
                    return HTTPSeeOther(location=request.route_url('login'))
                else:
                    firstname = request.POST.get('firstname', '')
                    lastname = request.POST.get('lastname', '')
                    uname = "{0} {1}".format(firstname.encode('utf-8'), lastname.encode('utf-8')).decode('utf-8')
                    newuser = User()
                    newuser.login = login
                    newuser.name = uname
                    newuser.password = hashlib.md5(salt+password).hexdigest()
                    request.dbsession.add(newuser)
                    request.session.flash({
                            'class' : 'success',
                            'text'  : u'Данные сохранены'
                            })

                    return HTTPSeeOther(location=request.route_url('home'))
                    
    return tpl

@view_config(route_name='home', renderer='../templates/hometemplate.jinja2')
def mainview(request):
    tpl = {}
    return tpl

@view_config(route_name='settings', renderer='../templates/settingstemplate.jinja2')
def settingsview(request):
    tpl = {}
    if not authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('home'))

    user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
    tpl.update({'authuser':user})
    
    #for admins
    if user.is_admin:
        users = request.dbsession.query(User).all()
        courses = request.dbsession.query(CourseElement).filter(CourseElement.parent == None).all()
        subscr = request.dbsession.query(Subscription).all()
        payments = request.dbsession.query(Payment).order_by(Payment.status).all()
        tpl.update({'users':users, 'courses':courses, 'subscr':subscr, 'payments':payments})
    
    # for authors
    elif user.is_author and not user.is_admin:
        #get author's courses
        courses = request.dbsession.query(CourseElement).filter(CourseElement.author_id == user.id).all()
        #get all subscriptions for author's courses
        subscr = request.dbsession.query(Subscription).join(CourseElement).filter(CourseElement.author_id==user.id).all()
        # get all user payments for author's courses
        payments = request.dbsession.query(Payment).join(Subscription).join(CourseElement).filter(CourseElement.author_id==user.id).order_by(Payment.status).all()
        # get all users, subscribed to author's courses
        users = request.dbsession.query(User).join(Subscription).filter(Subscription.cname.has(CourseElement.author_id==user.id)).all()
        tpl.update({'courses':courses, 'users':users, 'payments':payments, 'subscr':subscr})

    else:
        # for clients
        subscr = request.dbsession.query(Subscription).filter(Subscription.user == user.id).all()
        payments = request.dbsession.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.status).all()
        tpl.update({'subscr':subscr, 'payments':payments})

    return tpl


@view_config(route_name='subscrpause')
def subscrpauseview(request):
    if not authenticated_userid(request):
        request.session.flash({
                'class' : 'success',
                'text'  : u'Войдите или зарегистрируйтесь, чтобы подписаться на курс'
                })
        return HTTPSeeOther(location=request.route_url('login'))
    user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
    subid = None
    action = None
    mess = u"изменена"
    try:
        subid = int(request.matchdict['subscrid'])
        action = request.matchdict['action']
    except:
        request.session.flash({
                'class' : 'warning',
                'text'  : u'Что-то не так'
                })
        raise HTTPNotFound()
    if subid is not None and action is not None:
        subscr = request.dbsession.query(Subscription).filter(Subscription.user == user.id).filter(Subscription.id==subid).first()
        if action == "pause":
            subscr.is_paused = 1
            mess = u"приостановлена"
        if action == "unpause":
            subscr.is_paused = 0
            mess = u"возобновлена"
        if action == "cancel":
            subscr.is_cancelled = 1
            mess = u"отменена"
        if action == "restore":
            mess = u"восстановлена"
            subscr.is_cancelled = 0

        subscr.lastchanged = datetime.datetime.utcnow()
        request.dbsession.add(subscr)
        request.session.flash({
                'class' : 'success',
                'text'  : u'Подписка %s' % mess
                })
        return HTTPSeeOther(location=request.route_url('dashboard'))

    request.session.flash({
            'class' : 'warning',
            'text'  : u'Что-то не так'
            })
    return HTTPSeeOther(location=request.route_url('dashboard'))


@view_config(route_name='subscradd')
def subscraddview(request):
    # +человек заходит на сайт,
    # +нажимает подписаться
    # 
    # +проверяем залогинен ли он
    #
    # +если нет
    #   +перебрасываем на логин,
    #   +логиним или регистрируем, потом перебрасываем на страницу
    #   +подписки на курс
    # +если да
    # +смотрим на курс. если он в архиве или неопубликован, то 404 и перебрасываем на все курсы
    # +смотрим на подписки
    # +если подписан на этот курс, перебрасываем в dashboard 
    # +если нет, перебрасываем на страницу подписки на курс - форма оплаты
    # +на странице подписки показываем подробное описание курса, кол-во недель и пр. 
    # +первые две недели бесплатно, карточка не требуется.
    # человек оплачивает
    # если удачно, то 
    #     создаем новую подписку, добавляем ее и перебрасываем в dashboard,
    # если нет,
    #     перекидываем его на страницу оплаты с сообщением об ошибке и предложением попробовать снова
    # +готово

    tpl = {}
    cid = None

    if not authenticated_userid(request):
        request.session['redirectto'] = request.path
        request.session.flash({
                'class' : 'success',
                'text'  : u'Войдите или зарегистрируйтесь, чтобы подписаться на курс'
                })
        return HTTPSeeOther(location=request.route_url('login'))
    try:
        cid = int(request.matchdict['courseid'])
    except:
        request.session.flash({
                'class' : 'warning',
                'text'  : u'Что-то не так'
                })
        raise HTTPNotFound()

    if cid:
        course = request.dbsession.query(CourseElement).filter(CourseElement.id == cid).first()
        user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
        subscr = request.dbsession.query(Subscription).filter(Subscription.user == user.id).filter(Subscription.course_id==cid).first()

        if course.is_published and not course.is_archived:
            if subscr is None:
                # если не подписаны вообще
                # перекидываем на страницу оплаты
                return HTTPSeeOther(location=request.route_url('payment', action="send", courseid=course.id, userid=user.id))
            elif subscr.is_finished == 1:
                request.session.flash({
                        'class' : 'warning',
                        'text'  : u'Ваша подписка на курс %s закончилась %s, если хотите, можете продлить подписку' % (course.name, subscr.end)
                        })
                return HTTPSeeOther(location=request.route_url('payment', action="renew", courseid=course.id, userid=user.id, _query={"sid":subscr.id}))
                
            else:
                request.session.flash({
                        'class' : 'success',
                        'text'  : u'Вы уже подписаны на курс %s' % course.name
                        })
                
                return HTTPSeeOther(location=request.route_url('dashboard'))

    request.session.flash({
            'class' : 'warning',
            'text'  : u'Что-то не так'
            })
    raise HTTPNotFound()



@view_config(route_name='paymentcheck')
def paymentcheck(request):
    # тут проверяем платеж
    dbsess = request.dbsession
    request = request.decode('windows-1251')
    result = request.POST.get("WMI_ORDER_STATE")
    
    
    print "&"*80
    print request.POST
    print "&"*80


    if result=="Accepted":
        print "&"*80
        print request.POST
        print "&"*80
        userid = int(request.POST.get('uid'))
        paymentid = int(request.POST.get('pid'))
        subscrid = int(request.POST.get('sid'))
        courseid = int(request.POST.get('cid'))
        course = dbsess.query(CourseElement).filter(CourseElement.id == courseid).first()
        payment = dbsess.query(Payment).filter(Payment.id == paymentid).first()
        subscr = dbsess.query(Subscription).filter(Subscription.id == subscrid).first()
        if subscr is not None:
            startdate = datetime.datetime.utcnow()
            numweeks = len(course.children)
            enddate = startdate + datetime.timedelta(weeks=numweeks) - datetime.timedelta(days=1)
            subscr.is_paid = 1
            subscr.lastchanged = startdate
            subscr.end = enddate
            payment.status = "confirmed"
            dbsess.add(subscr)
            dbsess.add(payment)
            transaction.commit()
            resp = Response(body='WMI_RESULT=OK', content_type='text/plain')
        else:
            resp = Response(body='WMI_RESULT=OK&WMI_DESCRIPTION=No such subscription, stop trying', content_type='text/plain')
    else:
        resp = Response(body='WMI_RESULT=RETRY&WMI_DESCRIPTION=Something wrong, try again', content_type='text/plain')
        
    return resp

@view_config(route_name='payment', renderer='../templates/paymenttemplate.jinja2')
def paymentview(request):
    # тут отправляем платеж
    tpl = {}
    
    if not authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('login'))

    action = request.matchdict['action']
    cid = int(request.matchdict['courseid'])
    uid = int(request.matchdict['userid'])
    cfg = request.registry.settings
    merchid = cfg.get('merchantid')
    walleturl = cfg.get('walleturl')

    user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
    course = request.dbsession.query(CourseElement).filter(CourseElement.id == cid).first()
    

    if action == 'send':
        subscrtype = request.dbsession.query(SubscrType).filter(SubscrType.subscrtype == course.coursetype).first()
        payment_descr = u"ТЕСТ Оплата за подписку на курс %s, %s, %s ТЕСТ" % (course.name, user.login, subscrtype.comment)

        # создаем новую подписку только если не подписан
        alreadysubscribed = request.dbsession.query(Subscription).filter(Subscription.user == user.id).filter(Subscription.course_id==course.id).first()
        if alreadysubscribed is None:
            if subscrtype.subscrtype == "short":
                numweeks = len(course.children)
            else:
                numweeks = subscr.subscrtype.subscrtype.numweeks
            startdate = datetime.datetime.utcnow()
            enddate = startdate + datetime.timedelta(weeks=numweeks) - datetime.timedelta(days=1)
            fl = "status:test"
            newsubscr = Subscription(user=user.id, course_id=course.id, start=startdate, end=enddate, flags=fl, subscrtype_id=subscrtype.id)
            request.dbsession.add(newsubscr)
            request.dbsession.flush()
            newpayment = Payment(user_id=user.id, subscription_id=newsubscr.id, status='new', date=startdate, descr=payment_descr)
            request.dbsession.add(newpayment)
            request.dbsession.flush()
            tpl.update({
                    'course': course,
                    'merchid': merchid,
                    'price': subscrtype.price,
                    'sid': newsubscr.id,
                    'pid': newpayment.id,
                    'descr': payment_descr,
                    'courseid': cid,
                    'userid': uid,
                    'walleturl': walleturl,
                    })
        else:
            request.session.flash({
                    'class' : 'success',
                    'text'  : u'Вы уже полписаны на этот курс'
                    })

            return HTTPSeeOther(location=request.route_url('settings'))

    elif action == 'pay':
        sid = request.GET['sid']
        subscr = request.dbsession.query(Subscription).filter(Subscription.id == sid).first()
        tpl.update({
                'course': course,
                'merchid': merchid,
                'price': subscr.subscrtype.price,
                'sid': subscr.id,
                'pid': subscr.payment.id,
                'descr': subscr.payment.descr,
                'courseid': cid,
                'userid': uid,
                'walleturl': walleturl,
                })

    elif action == 'renew':
        # подписка закончилась, создаем новый платеж для этой подписки
        sid = request.GET['sid']
        subscr = request.dbsession.query(Subscription).filter(Subscription.id == sid).first()
        payment_descr = u"ТЕСТ Продление подписки на курс %s, %s, %s ТЕСТ" % (course.name, user.login, subscr.subscrtype.comment)

        startdate = datetime.datetime.utcnow()
        if subscr.subscrtype.subscrtype == "short":
            numweeks = len(course.children)
        else:
            numweeks = subscr.subscrtype.subscrtype.numweeks

        enddate = startdate + datetime.timedelta(weeks=numweeks) - datetime.timedelta(days=1)

        subscr.lastchanged = startdate
        subscr.end = enddate
        request.dbsession.add(subscr)

        newpayment = Payment(user_id=user.id, subscription_id=subscr.id, status='new', date=startdate, descr=payment_descr)
        request.dbsession.add(newpayment)
        request.dbsession.flush()

        tpl.update({
                'course': course,
                'merchid': merchid,
                'price': subscr.subscrtype.price,
                'sid': subscr.id,
                'pid': newpayment.id,
                'descr': payment_descr,
                'courseid': cid,
                'userid': uid,
                'walleturl': walleturl,
                })
    
    elif action == 'paycheck':
        sid = request.GET['sid']
        pid = request.GET['pid']
        subscr = request.dbsession.query(Subscription).filter(Subscription.id == sid).first()
        payment = request.dbsession.query(Payment).filter(Payment.id == pid).first()
        tpl.update({
                'course': course,
                'merchid': merchid,
                'price': subscr.subscrtype.price,
                'sid': sid,
                'pid': pid,
                'descr': payment.descr,
                'courseid': cid,
                'userid': uid,
                'walleturl': walleturl,
                })
        
    return tpl


@view_config(route_name='workout', renderer='../templates/workouttemplate.jinja2')
def workoutview(request):
    tpl = {}
    if not authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('login'))
    wktid = int(request.matchdict['wktid'])
    
    user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
    #get user subscriptions
    workout = request.dbsession.query(CourseElement).filter(CourseElement.id == wktid).filter(CourseElement.elemtype=="workout").first()
    if workout is not None:
        subscr = request.dbsession.query(Subscription).filter(Subscription.user == user.id).filter(Subscription.course_id == workout.parent.parent.id).first()
        if subscr is not None:
            tpl.update({"workout":workout})
            return tpl
    # проверяем подписку на этот курс
    # проверяем чтобы этот воркаут относился к подписанному
    # возвращаем воркаут
    
    raise HTTPNotFound()

@view_config(route_name='dashboard', renderer='../templates/dashboardtemplate.jinja2')
def dashboardview(request):
    tpl = {}
    if not authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('login'))

    user = request.dbsession.query(User).filter(User.login == authenticated_userid(request)).first()
    subscr = request.dbsession.query(Subscription).filter(Subscription.user == user.id).all()
    tpl.update({'subscr':subscr})
    
    return tpl

@view_config(route_name='resetpassword', renderer='../templates/resetpasswordtemplate.jinja2')
def resetpasswordview(request):
    tpl = {}

    if authenticated_userid(request):
        return HTTPSeeOther(location=request.route_url('home'))
    if request.POST:
        # третий шаг, сохраняем новый пароль и перезаписываем last_changed
        # if POST, validate params, reset password and redirect to the login page
        login = request.POST.get('login')
        token = request.POST.get('token')
        newpass = request.POST.get('password')
        csrf = request.POST.get('csrf')
        user = request.dbsession.query(User).filter(User.login == login).first()
        dbtoken  = hashlib.md5(user.password+str(user.lastchanged)).hexdigest()
        if token != dbtoken:
            request.session.flash({
                    'class' : 'info',
                    'text'  : u'Ваша ссылка устарела, попробуйте еще раз восстановить пароль'
                    })
            return HTTPSeeOther(location=request.route_url('login'))
        cfg = request.registry.settings
        salt = cfg.get('salt')
        user.password = hashlib.md5(salt+newpass).hexdigest()
        user.lastchanged = datetime.datetime.utcnow()
        request.dbsession.add(user)
        request.session.flash({
                'class' : 'success',
                'text'  : u'Новый пароль сохранен'
                })
        
        return HTTPSeeOther(location=request.route_url('login'))

        #do stuff
        #redirect to login

    elif 'token' in request.GET.keys():
        #второй шаг, приходим по ссылке из email
        # и заполняем новый пароль
        login = request.GET.get('login')
        token = request.GET.get('token')
        # проверка токена
        # !
        user = request.dbsession.query(User).filter(User.login == login).first()
        dbtoken  = hashlib.md5(user.password+str(user.lastchanged)).hexdigest()
        if token != dbtoken:
            request.session.flash({
                    'class' : 'info',
                    'text'  : u'Ваша ссылка устарела, попробуйте еще раз восстановить пароль'
                    })
            return HTTPSeeOther(location=request.route_url('login'))

        # return new password form
        # with hidden params
        tpl.update({'login':user.login,
                    'token':token
                    })
        return tpl
    else:
        #первый шаг, создаем токен
        to = request.GET.get('login')
        fr = 'noreply@manatee.trololo.info'
        replyto = 'a@manatee.trololo.info'
        msg = email.mime.multipart.MIMEMultipart()
        msg['from']=fr
        msg.add_header('reply-to', replyto)
        msg['to']=to
        msg['subject'] = "Сброс пароля на MakeMeStrong.ru"
        message = """Кто-то воспользовался формой сброса пароля, указав ваш эл. адрес, {0}
Если это были не вы, просто проигнорируйте это сообщение. 

Для сброса пароля пройдите по ссылке: {1}

С уважением, команда MakeMeStrong.
    """
        user = request.dbsession.query(User).filter(User.login == to.encode('utf-8')).first()
        if user is not None:
            token = hashlib.md5(user.password+str(user.lastchanged)).hexdigest()
            message = message.format(user.login, request.route_url('resetpassword', _query={'login':user.login, 'token':token}))
            msgtext = MIMEText(message, 'plain')
            msg.attach(msgtext)
            serv = smtplib.SMTP('localhost')
            serv.sendmail(fr, to, msg.as_string())
            serv.quit()
        else:
            request.session.flash({
                    'class' : 'info',
                    'text'  : u'Похоже, что такого адреса у нас нет, попробуйте сначала зарегистрироваться'
                    })
            return HTTPSeeOther(location=request.route_url('login'))

    
    return HTTPSeeOther(location=request.route_url('login'))
    #return tpl


def generatetree(req, obj):
    def getparent(obj):
        if obj.parent is not None:
            return getparent(obj.parent)
        else:
            return obj.id

    def jsondata(req, obj):
        strtempl = u"{0} {1} "
        addstr = u"{0} "
        btn_template = u"""<a class="btn btn-sm" style="text-decoration:none;" href="{0}" role="butto"> {1}</a>"""
        btn_edit = btn_template.format(req.route_url('courseaction', courseid=getparent(obj), args=('edit', obj.elemtype, obj.id)), u"Править")
        btn_delete = btn_template.format(req.route_url('courseaction', courseid=obj.id, args=('delete', obj.elemtype, obj.id)), u"Удалить")
        btn_add = btn_template.format(req.route_url('courseaction', courseid=obj.id, args=('new', obj.elemtype, obj.id)), u"Добавить")
        nodetext = strtempl.format(obj.trelemtype, obj.childindex)
        if obj.trweektype is not None:
            nodetext = nodetext + addstr.format(obj.trweektype)
            
        if obj.name is not None:
            nodetext = nodetext + addstr.format(obj.name)

        nodetext = nodetext + btn_edit + btn_delete + btn_add
        
        return {"text":nodetext, "nodes":[jsondata(req, ch) for ch in obj.children]}

    def jsontree(req, obj):
        outlist = []
        if obj.parent is None:
            for ch in obj.children:
                outlist.append(jsondata(req, ch))
        return json.dumps(outlist, indent=4)
       
    return jsontree(req, obj)
