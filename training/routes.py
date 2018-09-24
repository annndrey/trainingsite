def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('register', '/register')
    config.add_route('logout', '/logout')
    config.add_route('dashboard', '/dashboard')
    config.add_route('settings', '/settings')
    config.add_route('resetpassword', '/resetpassword')

    config.add_route('showone', '/view/{what}/{id:\d+}')
    config.add_route('showall', '/view/{what}')
    
    config.add_route('new', '/new/{what}')
    config.add_route('edit', '/edit/{what}/{id:\d+}')
    config.add_route('delete', '/delete/{what}/{id:\d+}')
    config.add_route('about', '/about')

    #for course modification
    config.add_route('modifycourse', '/modify/{courseid:\d+}')
    config.add_route('courseaction', '/mod/{courseid:\d+}/*args')
    
    #subscriptions
    config.add_route('subscradd', '/subscribe/{courseid:\d+}')
    config.add_route('subscrpause', '/sub/{action}/{subscrid:\d+}')
    config.add_route('payment', '/payment/{action}/{courseid:\d+}/{userid:\d+}')
    config.add_route('paymentcheck', '/check')

    #workouts
    config.add_route('workout', '/wkt/{wktid:\d+}')
    
