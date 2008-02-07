import gtk

RIGHT_CLIC = 3

class Contextual(gtk.Menu):

    RIGHT_CLIC = 3

    def __init__(self, items_list):
        gtk.Menu.__init__(self)
        for it in items_list:
            item = gtk.MenuItem(it)
            self.append(item)
            item.connect("activate", self.connector, it)
            item.show()
        self.show()

    def connector(self, widget, string):
        print string

def box_event(widget, event):
    if event.type == gtk.gdk.BUTTON_PRESS:
        if event.button == RIGHT_CLIC:
            widget.popup(parent_menu_shell=None, parent_menu_item=None, func=None, button=event.button, activate_time=event.time, data=None)
            return True
    return False

if __name__ == '__main__':
    w = gtk.Window(gtk.WINDOW_TOPLEVEL)
    w.set_size_request(200, 200)
    w.connect("delete_event", lambda x,e : gtk.main_quit())
    hbox = gtk.HBox()
    w.add(hbox)
    menu = Contextual(["1", "2", "3"])
    bouton = gtk.Button("TEST")
    bouton.connect_object("event", box_event, menu)
    hbox.pack_end(bouton, True, True, 2)
    bouton.show()
    hbox.show()
    w.show()
    gtk.main()


