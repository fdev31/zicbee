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

from simplejson import dumps as simplejson
from cjson import encode as cjson
from demjson import encode as demjson

from itertools import count
cnt = count()

#def test(stuff):
#    cnt.next()
#    return repr(stuff)

if __name__ == '__main__':
    modules = ('cjson', 'simplejson', 'demjson')
    from timeit import Timer
#    modules = ('test',)
    def _get_best(t, num, best_val, best_time):
        tnum = t.timeit(100)
        if best_val is None:
            best_val = num
            best_time = tnum
        elif best_time > tnum:
            best_time = tnum
            best_val = num
        print "%d = %.2fs"%(num, tnum)
        return (best_val, best_time)

    for mod_name in modules:
        print mod_name

        best_val = None
        best_time = None
        print "test1 (one shot)"
        t = Timer('test1(%s)'%(mod_name), 'from bensh import test1, %s'%(', '.join(modules)))
        best_val, best_time = _get_best(t, 1, best_val, best_time)

        best_val = None
        best_time = None
        for num in xrange(2, 1000, 50):
            t = Timer('test2(%s, %d); cnt.next()'%(mod_name, num), 'from bensh import cnt, test2, %s'%(', '.join(modules)))
            best_val, best_time = _get_best(t, num, best_val, best_time)
        print "BEST VAL for N=%d"%best_val

    print cnt.next()

