from zicbee_lib.resources import resource_filename
import pynotify
import pygtk
pygtk.require('2.0')
import gtk

icons = 'connect convert dialog-info dialog-error find media-pause media-next media-play media-previous'.split()
bee_icon = resource_filename('zicbee.ui.notify', 'bee_icon.png')

def notify(title, description=None, icon=None, timeout=750):
    if icon in icons:
        iname = "gtk-"+icon
    else:
        iname = 'file://%s'%bee_icon

    pynotify.init("SimpleNotifier")
    n = pynotify.Notification(title, description, iname)
    n.set_urgency(pynotify.URGENCY_LOW)
    n.set_timeout=(timeout)
    n.show()


if __name__ == '__main__':
    notify('Title1', 'descr1\nfoo\tbar\nblah\ttoto', icon='dialog-info')
#    notify('Title2', 'descr2', icon='media-play', timeout=200)
#    notify('Title3', 'descr3', '/tmp/iconbee.png')

