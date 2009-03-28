__all__ = ['jdump', 'jload', 'clean_path', 'safe_path', 'parse_line', 'duration_tidy', 'get_help_from_func', 'DEBUG']

import traceback
import itertools
import inspect
import string
import sys
import os
from os.path import expanduser, expandvars, abspath
from zicbee.core.debug import log # forward some symbols
import logging

# Filename path cleaner
def clean_path(path):
    return expanduser(abspath(expandvars(path)))

def safe_path(path):
    return path.replace(os.path.sep, ' ')

# int (de)compacter [int <> small str convertors]
# convert to base62...
base = 62
chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

def compact_int(ival):
    result = []
    rest = ival
    b = base
    while True:
        int_part, rest = divmod(rest, b)
        result.append(chars[rest])
        if not int_part:
            break
        rest = int_part
    return "".join(reversed(result))

def uncompact_int(str_val):
    # int(x, base) not used because it's limited to base 36
    unit = 1
    result = 0
    for char in reversed(str_val):
        result += chars.index(char) * unit
        unit *= base
    return result

################################################################################

#
# Try to get the most performant json backend
#
# cjson:
# 10 loops, best of 3: 226 msec per loop
# simplejson:
# 1 loops, best of 3: 10.3 sec per loop
# demjson:
# 1 loops, best of 3: 65.2 sec per loop
#

json_engine = None
try:
    from json import dumps as jdump, loads as jload
    json_engine = "python's built-in"
except ImportError:
    try:
        from cjson import encode as jdump, decode as jload
        json_engine = 'cjson'
    except ImportError:
        try:
            from simplejson import dumps as jdump, loads as jload
            json_engine = 'simplejson'
        except ImportError:
            from demjson import encode as jdump, decode as jload
            json_engine = 'demjson'

sys.stderr.write("using %s engine.\n"%json_engine)
################################################################################

_plur = lambda val: 's' if val > 1 else ''

def duration_tidy(orig):
    minutes, seconds = divmod(orig, 60)
    if minutes > 60:
        hours, minutes = divmod(minutes, 60)
        if hours > 24:
            days, hours = divmod(hours, 24)
            return '%d day%s, %d hour%s %d min %02.1fs.'%(days, _plur(days), hours, _plur(hours), minutes, seconds)
        else:
            return '%d hour%s %d min %02.1fs.'%(hours, 's' if hours>1 else '', minutes, seconds)
    else:
        return '%d min %02.1fs.'%(minutes, seconds)
    if minutes > 60:
        hours = int(minutes/60)
        minutes -= hours*60
        if hours > 24:
            days = int(hours/24)
            hours -= days*24
            return '%d days, %d:%d.%ds.'%(days, hours, minutes, seconds)
        return '%d:%d.%ds.'%(hours, minutes, seconds)
    return '%d.%02ds.'%(minutes, seconds)

################################################################################
# documents a function automatically

def get_help_from_func(cmd):
    """
    returns a tuple (str::tidy doc, bool::is_remote) from a function
    """
    arg_names, not_used, neither, dflt_values = inspect.getargspec(cmd)
    is_remote = any(h for h in arg_names if h.startswith('host') or h.endswith('host'))

    if cmd.__doc__:
        if dflt_values is None:
            dflt_values = []
        else:
            dflt_values = list(dflt_values)

        # Ensure they have the same length
        if len(dflt_values) < len(arg_names):
            dflt_values = [None] * (len(dflt_values) - len(arg_names))
#            map(None, arg_names, dflt_values)

        doc = '::'.join('%s%s'%(arg_name, '%s'%('='+str(arg_val) if arg_val is not None else '')) for arg_name, arg_val in itertools.imap(None, arg_names, dflt_values))

        return ("%s\n%s\n"%(
            ("%s[::%s]"%(cmd.func_name[3:], doc) if len(doc) > 1 else cmd.func_name[3:]), # title
            '\n'.join('   %s'%l for l in cmd.__doc__.split('\n') if l.strip()), # body
        ), is_remote)
    else:
        return (cmd.func_name[3:], is_remote)

################################################################################
# line parser

properties = []
for name in 'score tags length artist title album filename'.split():
    properties.append(name)
    properties.append(name.title())
del name

def _find_property(line):
    tab = line.rsplit(None, 1)
    for prop in properties:
        if prop == tab[-1]:
            if len(tab) == 1:
                return line
            else:
                return tab[-1], tab[0].strip()

def _conv_line(txt):
    """ Converts a syntax string to an easy to parse array of datas
    data consists of str or (str, str) tuples
    str values are operators like: or, and, !or, (, ), etc...
    tuples are: key: value
    """
    # TODO: replace with a real parser ?
    split_line = txt.split(':')
    log.debug('split line: %s'% split_line)

    if len(split_line) > 1:
        ret = []
        attr = None
        for elt in split_line:
            if attr is None:
                if elt[0] == '(':
                    elt = elt[1:].strip()
                    ret.append('(')
                attr = elt
                log.debug('attr: %s'%elt)
            else:
                props = _find_property(elt)
                log.debug('props: %s'%repr(props))
                if props:
                    # get init vars
                    name, val = props
                    vals = val.rsplit(None, 1)
                    # set defaults
                    bin_operator = 'and'
                    next_is_grouped = False
                    end_of_group = False
                    if len(vals) > 1: # check the last element
                        if vals[1] == '(':
                            vals = vals[0].rsplit(None, 1)
                            next_is_grouped = True
                        if vals[1] in ('or', 'and', 'or!', 'and!'):
                            val = vals[0]
                            if val[-1] == ')':
                                val = val[:-1].strip()
                                end_of_group = True
                            bin_operator = vals[1]
                            if bin_operator[-1] == '!':
                                bin_operator = bin_operator[:-1] + ' not'
                    log.debug('ret.append(%r, %r)', attr, val)
                    ret.append( (attr, val) )
                    if end_of_group:
                        ret.append(')')
                    log.debug('ret.append(%r)', bin_operator)
                    ret.append( bin_operator )
                    attr = name
                    if next_is_grouped:
                        ret.append('(')
                else:
                    elt = elt.strip()
                    end_of_group = False
                    if elt[-1] == ')':
                        elt = elt[:-1].strip()
                        end_of_group = True
                    log.debug('noprops: %r / %r', attr, repr(elt))
                    ret.append( (attr, elt.strip()) )
                    if end_of_group:
                        ret.append(')')
        log.debug('ret: %s'%txt)
        return ret
    else:
        log.debug('txt: %s'%txt)
        return txt

RAW_ATTRS = ('filename',)

def parse_line(line):
    """ Gets a line in the form "<name>: value <other name>: value"
   Returns an evaluable python string """
    ret = _conv_line(line)
    log.debug('RET: %s'%repr(ret))
    # string (simple) handling
    if isinstance(ret, basestring):
        if ret:
            return ('%(t)s in artist or %(t)s in title or %(t)s in filename or %(t)s in album'%dict(t='"%s"'%ret.replace('"', r'\"')), {})
        else:
            return ('1', {})
    # complex search
    varnames = list(string.ascii_letters)
    args = {}
    str_list = []

    def try_dec(txt):
        try:
            return txt.decode('utf-8')
        except UnicodeDecodeError:
            return txt.decode('latin1')

    for pattern in ret:
        if isinstance(pattern, basestring):
            log.debug('str_list.append("%s")', pattern)
            str_list.append(pattern)
        else:
            attr_name, value = pattern
            var_name = varnames.pop(0)
            if attr_name in ('length', 'score', 'id'):
                is_id = attr_name == 'id'
                if is_id:
                    attr_name = '__id__'
                # numeric
                modifier = ''
                while value[0] in '>=<':
                    modifier += value[0]
                    value = value[1:]

                if is_id:
                    try:
                        value = str(uncompact_int(value))
                    except Exception, e:
                        log.error("uncompact_int: %s"%e)

                log.debug('str_list.append("%r %r %r")', attr_name, modifier or '==', var_name)
                str_list.append('%s %s %s'%(attr_name, modifier or '==', var_name))
                args[var_name] = eval(value)
            else:
                if attr_name in RAW_ATTRS:
                    value = str(value)

                # If attr name is capitalized, no case-unsensitive search
                if attr_name[0].islower():
                    value = value.lower()
                    attr_name += '.lower()'
                else:
                    attr_name = attr_name.lower()
                str_list.append('%s in %s'%(try_dec(repr(value)), attr_name))
                log.debug('str_list.append(%s)'%str_list[-1])
    return ' '.join(str_list), args

