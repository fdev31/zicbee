__all__ = ['parse_line', 'extract_props']

import itertools
import os
import string
from zicbee_lib.debug import log
from zicbee_lib.formats import uncompact_int
from zicbee.remote_apis import ASArtist

################################################################################
# line parser

properties = []
for name in 'id score tags length artist title album filename'.split():
    properties.append(name)
    properties.append(name.title())
del name

def _find_property(line, property_list=None):
    tab = line.rsplit(None, 1)
    for prop in property_list or properties:
        if tab[-1] in (prop, prop[:2]):
            if len(tab) == 1:
                return prop
            else:
                return prop, tab[0].strip()

def extract_props(line, property_list):
    """ extract a set of properties in a search string
    return: (new_search_string, [(prop1, value1), (prop2, value2), ...])
    """
    props = properties[:]
    props.extend(property_list)
    conv_line = _conv_line(line, props)
    if isinstance(conv_line, basestring):
        return ( conv_line, [] )
    ret_props = (conv for conv in conv_line if isinstance(conv, tuple) and conv[0] in property_list)
    new_conv_line = [conv for conv in conv_line if not isinstance(conv, tuple) or conv[0] not in property_list]
    try:
        if not isinstance(new_conv_line[0], tuple):
            new_conv_line.pop(0)
        if not isinstance(new_conv_line[-1], tuple):
            new_conv_line.pop(-1)
    except IndexError:
        pass

    new_line = " ".join(conv if not isinstance(conv, tuple) else ": ".join(conv) for conv in new_conv_line)
    return (new_line, ret_props)

def _conv_line(txt, property_list=None):
    """ Converts a syntax string to an easy to parse array of datas
    data consists of str or (str, str) tuples
    str values are operators like: or, and, !or, (, ), etc...
    tuples are: (key: value)

    NOTE: if there is no operator involved, the passed value is returned unmodified!
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
                attr = _find_property(elt, property_list)
                log.debug('attr: %s'%attr)
            else:
                props = _find_property(elt, property_list)
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

    automatic_playlist = False

    if "*AUTO" in line: # special keyword
        if "*AUTO*" in line: # Just *AUTO*
            line = line.replace('*AUTO*', '')
            automatic_playlist_results = 10
        else: # *AUTO <size factor>* syntax
            idx = s.index('*AUTO')+5 # 5 = len(*AUTO)
            subidx = idx+line[idx:].index('*')
            automatic_playlist_results = int(line[idx:subidx])
            banned_characters = range(idx-5, subidx+1) # 5 = len(*AUTO) ; 1 = len(*)
            line = ''.join(c for i, c in enumerate(line) if i not in banned_characters)

        automatic_playlist = True

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

                var_value = eval(value)
                modif = modifier or '=='
                log.debug('str_list.append("%r %r %r")', attr_name, modif, var_name)
                str_list.append('%s %s %s'%(attr_name, modif, var_name))
                args[var_name] = var_value

            else:
                if attr_name in RAW_ATTRS:
                    value = str(value)

                # If attr name is capitalized, no case-unsensitive search
                if attr_name[0].islower():
                    value = value.lower()
                    attr_name += '.lower()'
                else:
                    attr_name = attr_name.lower()

                attr_value = try_dec(repr(value))
                str_list.append('%s in %s'%(attr_value, attr_name))
                log.debug('str_list.append(%r)'%str_list[-1])

                if automatic_playlist and attr_name.startswith('artist'):
                    count_answers = itertools.count(0)
                    artist_infos = ASArtist(value)
                    for artist in artist_infos.getSimilar():
                        artist = artist[1].lower()
                        if count_answers.next() > automatic_playlist_results:
                            break
                        str_list.append('or %r in artist.lower()'%(artist))
                        log.debug('str_list.append(%s)'%str_list[-1])
                        # TODO: return the magic artists list so we can start doing some black magic in dbe module
                        # the goal is to use the autotracks too (heuristic: 50% best songs + 50% random)

    return ' '.join(str_list), args

