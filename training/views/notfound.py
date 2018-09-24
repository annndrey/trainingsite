from pyramid.view import notfound_view_config
from pyramid.security import authenticated_userid

@notfound_view_config(renderer='../templates/404.jinja2')
def notfound_view(request):
    tpl = {}
    request.response.status = 404
    return tpl
