import string

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

# line parser

properties = []
for name in 'length artist title album filename'.split():
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
    split_line = txt.split(':')
    ret = []
    if len(split_line) > 1:
        attr = None
        for elt in split_line:
            if attr is None:
                attr = elt
            else:
                props = _find_property(elt)
                if props:
                    name, val = props
                    vals = val.rsplit(None, 1)
                    bin_operator = 'and'
                    if len(vals) > 1:
                        if vals[1] in ('or', 'and'):
                            val = vals[0]
                            bin_operator = vals[1]

                    if attr[0].islower():
                        attr += '.lower()'
                        val = val.lower()
                    attr = attr.lower()
                    ret.append( (attr, val) )
                    ret.append( bin_operator )
                    attr = name
                else:
                    if attr[0].islower():
                        attr += '.lower()'
                        elt = elt.lower()
                    attr = attr.lower()
                    ret.append( (attr, elt.strip()) )
        return ret
    else:
        return txt

def parse_line(line):
    ret = _conv_line(line)
    # string (simple) handling
    if isinstance(ret, basestring):
        if ret:
            return ('"%s"'%ret, {})
        else:
            return ('1', {})
    # complex search
    varnames = list(string.ascii_letters)
    args = {}
    str_list = []
    for pattern in ret:
        if isinstance(pattern, basestring):
            str_list.append(pattern)
        else:
            attr_name, value = pattern
            var_name = varnames.pop(0)
            if attr_name in ('length',):
                # numeric
                modifier = ''
                while value[0] in '>=<':
                    modifier += value[0]
                    value = value[1:]

                str_list.append('%s %s %s'%(attr_name, modifier or '==', var_name))
                args[var_name] = eval(value)
            else:
                str_list.append('"%s" in %s'%(value.replace('"', r'\"'), attr_name))
    return ' '.join(str_list), args

