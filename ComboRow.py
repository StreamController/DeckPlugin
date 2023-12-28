# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class ComboRow(Adw.PreferencesRow):
    def __init__(self, title, model: Gtk.ListStore, **kwargs):
        super().__init__(title=title, **kwargs)
        self.model = model

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                margin_start=10, margin_end=10,
                                margin_top=10, margin_bottom=10)
        self.set_child(self.main_box)

        self.label = Gtk.Label(label=title, hexpand=True, xalign=0)
        self.main_box.append(self.label)


        self.combo_box = Gtk.ComboBox.new_with_model(self.model)
        self.main_box.append(self.combo_box)