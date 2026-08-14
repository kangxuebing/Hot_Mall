from jinja2 import Environment
from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage

def jinja2_url(view_name, *args, **kwargs):
    """Custom url function for Jinja2 that handles positional arguments correctly"""
    # Handle the case where args is passed as a keyword argument (like in base.html)
    if 'args' in kwargs:
        actual_args = kwargs.pop('args')
        try:
            return reverse(view_name, args=actual_args, kwargs=kwargs)
        except:
            pass
    
    # Try different combinations
    try:
        # First try with positional args
        if args:
            return reverse(view_name, args=args, kwargs=kwargs)
    except:
        pass
    
    try:
        # Then try with args as kwargs
        if args:
            # Assume positional args should be passed as pk
            return reverse(view_name, kwargs=dict(kwargs, pk=args[0] if args else None))
    except:
        pass
    
    try:
        # Finally try with no args
        return reverse(view_name, kwargs=kwargs)
    except:
        pass
    
    # If all else fails, raise an error
    raise Exception(f"Could not reverse URL for {view_name} with args={args}, kwargs={kwargs}")

def jinja2_environment(**options):
    """jinja2环境"""
    # 创建环境对象
    env = Environment(**options)
    # 自定义语法：{{ static('静态文件相对路径') }} {{ url('路由的命名空间') }}
    env.globals.update({
        'static': staticfiles_storage.url,   # 获取静态文件的前缀
        'url': jinja2_url,  						# 反向解析
    })
    env.filters['add_class'] = lambda field, css_class: field.as_widget(attrs={"class": css_class})
    # 返回环境对象
    return env
