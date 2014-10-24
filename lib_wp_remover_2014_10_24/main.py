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

import argparse
from . import wp_remover

def try_print(*args, **kwargs):
    try:
        return print(*args, **kwargs)
    except (ValueError, OSError):
        pass

def on_begin(event_ctx):
    try_print('{}: begin'.format(event_ctx.post_url))

def on_done(event_ctx):
    try_print('{}: done'.format(event_ctx.post_url))

def on_error(event_ctx):
    try_print('{}: error: {}'.format(event_ctx.post_url, event_ctx.error_str))

def main():
    parser = argparse.ArgumentParser(
            description='utility for removing posts from WordPress blogs',
            )
    
    parser.add_argument(
            'accs_path',
            metavar='ACC-LIST-PATH',
            help='path to file with account list (format CSV: "email","email_password","blog_url","username","password")',
            )
    parser.add_argument(
            'posts_path',
            metavar='POST-LIST-PATH',
            help='path to file with post url list to delete',
            )
    
    args = parser.parse_args()
    
    wp_remover.wp_remove(
            args.accs_path,
            args.posts_path,
            on_begin=on_begin,
            on_done=on_done,
            on_error=on_error,
            )
    
    try_print('done!')
