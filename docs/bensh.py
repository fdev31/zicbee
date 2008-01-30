#def fill():
#    inp = []
#    for name in 'A B C D E F G H'.split():
#        for val in xrange(10):
#            inp.append('%s%d'%(name, val))
#    return inp

def test1(test_fn):
    try:
        for n in xrange(10000):
            test_fn('A%d'%n)
    except Exception, e:
        print "E:", e

def test2(test_fn, nb):
    cumul = []
    for n in xrange(10000):
        cumul.append(n)
        if n>0 and nb%100 == 0:
            test_fn('[%s]'%(','.join('A%d'%n for n in cumul)))
            print len(cumul)
            cumul = []
    if cumul:
        test_fn('[%s]'%(','.join('A%d'%n for n in cumul)))

def test3(test_fn, nb):
    result = []
    cumul = []
    for n in xrange(10000):
        cumul.append(n)
        if n>0 and nb%100 == 0:
            res = test_fn('[%s]'%(','.join('A%d'%n for n in cumul)))
            result.extend(res)
            cumul = []
    if cumul:
        res = test_fn('[%s]'%(','.join('A%d'%n for n in cumul)))
        result.extend(res)

    return result

from simplejson import dumps as simplejson
from cjson import encode as cjson
from demjson import encode as demjson

from itertools import count

if __name__ == '__main__':
    modules = ('cjson', 'simplejson', 'demjson')
    from timeit import Timer
    def _get_best(name, mod_name, modules, num, best_val, best_time):
        if isinstance(num, str):
            cmd = '%s(%s)'%(name, mod_name)
        else:
            cmd = '%s(%s, %s)'%(name, mod_name, repr(num))
        t = Timer(cmd,
                'from bensh import %s, %s'%(name, ', '.join(modules)))
        tnum = t.timeit(100)
        if best_val is None:
            best_val = num
            best_time = tnum
        elif best_time > tnum:
            best_time = tnum
            best_val = num
        print "%s = %.2fs"%('%%%d'%num if isinstance(num, int) else num, tnum)
        return best_val, best_time

    def _full_bensh(module_name):
        print module_name

        print "method1 (direct):"
        best_val = None
        best_time = None
        _get_best('test1',
                module_name, modules,
                'direct',
                best_val, best_time)

#        print "method2:"
#        best_val = None
#        best_time = None
#        for num in xrange(2, 1000, 50):
#            best_val, best_time = _get_best('test2',
#                    module_name, modules,
#                    num,
#                    best_val, best_time)
#        print "the BEST VAL is for N=%s"%best_val

        print "method3:"
        best_val = None
        best_time = None
        for num in xrange(2, 1000, 50):
            best_val, best_time = _get_best('test3',
                    module_name, modules,
                    num,
                    best_val, best_time)
        print "the BEST VAL is for N=%s"%best_val

    for mod_name in modules:
        _full_bensh(mod_name)


