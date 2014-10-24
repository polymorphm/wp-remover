# -*- mode: python; coding: utf-8 -*-
#
# Copyright (c) 2014 Andrej Antonov <polymorphm@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import queue
import threading
from xmlrpc import client as xmlrpc
from urllib import parse as url_parse
from urllib import request
from . import get_items

class WpRemoveEventCtx:
    pass

class WpRemoveError(Exception):
    pass

def norm_blog_url(blog_url):
    assert isinstance(blog_url, str)
    
    if not blog_url.startswith('//') and \
            not blog_url.startswith('http://') and \
            not blog_url.startswith('https://'):
        blog_url = '//{}'.format(blog_url)
    
    if not blog_url.startswith('http:') and \
            not blog_url.startswith('https:'):
        blog_url = 'http:{}'.format(blog_url)
    
    if '?' in blog_url:
        blog_url = blog_url[:blog_url.find('?')]
    
    if not blog_url.endswith('/'):
        blog_url = '{}/'.format(blog_url)
    
    return blog_url

def parse_page_id(page_url):
    assert isinstance(page_url, str)
    
    splited_page_url = url_parse.urlsplit(page_url)
    
    if not splited_page_url.query:
        return
    
    parsed_query = url_parse.parse_qs(splited_page_url.query)
    page_id_list = parsed_query.get('page_id', [])
    
    if not page_id_list:
        return
    
    try:
        page_id = int(page_id_list[0])
    except ValueError:
        page_id = None
    
    return page_id

def safe_request(req):
    assert isinstance(req, request.Request)
    
    q = queue.Queue()
    
    def safe_request_func():
        data = None
        error = None
        
        try:
            opener = request.build_opener()
            res = opener.open(req, timeout=20.0)
            data = res.read(10000000)
        except Exception as e:
            error = '{}: {}'.format(type(e), str(e))
        
        q.put((data, error))
    
    threading.Thread(target=safe_request_func, daemon=True).start()
    data, error = q.get()
    
    return data, error

def wp_remove(accs_path, posts_path, on_begin=None, on_done=None, on_error=None):
    acc_csv = get_items.get_finite_items(accs_path, is_csv=True)
    post_url_list = get_items.get_random_finite_items(posts_path)
    
    acc_blog_table = {}
    
    for acc_line in acc_csv:
        if len(acc_line) != 5:
            continue
        
        acc_email, acc_email_pass, acc_blog_url, acc_username, acc_password = \
                acc_line
        acc_blog_url = norm_blog_url(acc_blog_url)
        acc_blog_table[acc_blog_url] = acc_username, acc_password
    
    for post_url in post_url_list:
        if on_begin is not None:
            event_ctx = WpRemoveEventCtx()
            event_ctx.post_url = post_url
            
            on_begin(event_ctx)
        
        try:
            page_id = parse_page_id(post_url)
            
            if not page_id:
                raise WpRemoveError('missing page_id')
            
            blog_url = norm_blog_url(post_url)
            acc_username, acc_password = acc_blog_table.get(blog_url, (None, None))
            
            if not acc_username or not acc_password:
                raise WpRemoveError('missing acc_username or missing acc_password')
            
            xmlrpc_data = xmlrpc.dumps(
                ('', page_id, acc_username, acc_password, False),
                'metaWeblog.deletePost',
                )
            
            req = request.Request(
                    url_parse.urljoin(blog_url, 'xmlrpc.php'),
                    data=xmlrpc_data.encode('utf-8', 'replace'),
                    headers={
                            'Content-Type': 'application/xml;charset=utf-8',
                            },
                    )
            resp_data, resp_error = safe_request(req)
            
            if resp_error:
                raise WpRemoveError('request error: {}'.format(resp_error))
            
            try:
                resp_params, resp_method = xmlrpc.loads(resp_data.decode('utf-8', 'replace'))
            except xmlrpc.Fault as e:
                raise WpRemoveError('{}: {}'.format(type(e), str(e)))
            
            if len(resp_params) != 1 or \
                    not isinstance(resp_params[0], bool) or \
                    not resp_params[0]:
                raise WpRemoveError('fail')
            
            if on_done is not None:
                event_ctx = WpRemoveEventCtx()
                event_ctx.post_url = post_url
                
                on_done(event_ctx)
        except WpRemoveError as e:
            if on_error is not None:
                event_ctx = WpRemoveEventCtx()
                event_ctx.post_url = post_url
                event_ctx.error_str = str(e)
                
                on_error(event_ctx)
