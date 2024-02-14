from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

import sys
import os
from PIL import Image
from loguru import logger as log

# Add plugin to sys.paths
sys.path.append(os.path.dirname(__file__))

# Import globals
import globals as gl

# Import own modules
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page


from plugins.dev_core447_DeckPlugin.ComboRow import ComboRow


# Import signals
from src.backend.PluginManager import Signals

class ChangePage(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.connect(signal=Signals.PageRename, callback=self.on_page_rename)

        self.set_default_image(Image.open(os.path.join(self.plugin_base.PATH, "assets", "folder.png")))
    def on_ready(self):
        # Ensures that there is always one page selected
        settings = self.get_settings()
        settings.setdefault("selected_page", gl.page_manager.get_pages()[0])
        self.set_settings(settings)

    def get_config_rows(self) -> list:
        self.page_model = Gtk.ListStore.new([str, str])
        # self.page_selector = Adw.ComboRow(model=self.page_model)
        # \Adw.ComboRow(model=self.page_model, title="Page:",
                                        #   subtitle="Select page to swtich to")
        self.page_selector_row = ComboRow(model=self.page_model, title="Page:")

        self.page_selector_cell_renderer = Gtk.CellRendererText()
        self.page_selector_row.combo_box.pack_start(self.page_selector_cell_renderer, True)
        self.page_selector_row.combo_box.add_attribute(self.page_selector_cell_renderer, "text", 0)
        
        self.load_page_model()

        self.load_config_defaults()

        # self.page_selector.connect("notify::selected-item", self.on_change_page)
        self.page_selector_row.combo_box.connect("changed", self.on_change_page)

        return [self.page_selector_row]
        

    def load_page_model(self):
        for page in gl.page_manager.get_pages():
            display_name = os.path.splitext(os.path.basename(page))[0]
            self.page_model.append([display_name, page])

    def load_config_defaults(self):
        settings = self.get_settings()
        if settings == None:
            return
        
        # Update page selector
        selected_page = settings.setdefault("selected_page", None)
        self.set_selected(selected_page)

    def set_selected(self, page_path: str) -> None:
        for i, row in enumerate(self.page_model):
            if row[1] == page_path:
                self.page_selector_row.combo_box.set_active(i)
                return
            
        self.page_selector_row.combo_box.set_active(-1)
        

    def on_change_page(self, combo, *args):
        page_path = self.page_model[combo.get_active()][1]
        

        settings = self.get_settings()
        settings["selected_page"] = page_path
        self.set_settings(settings)

    def on_key_down(self):
        page_path = self.get_settings().get("selected_page")
        page = gl.page_manager.get_page(page_path, deck_controller = self.deck_controller)
        self.deck_controller.load_page(page)

    def on_page_rename(self, old_path: str, new_path: str):
        settings = self.get_settings()
        if settings.get("selected_page") == old_path:
            settings["selected_page"] = new_path
            self.set_settings(settings)

            if hasattr(self, "page_model"):
                # Update page model
                self.page_selector_row.combo_box.disconnect_by_func(self.on_change_page)
                self.page_model.clear()
                self.load_page_model()
                self.set_selected(new_path)
                self.page_selector_row.combo_box.connect("changed", self.on_change_page)

class GoToSleep(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.set_default_image(Image.open(os.path.join(self.plugin_base.PATH, "assets", "sleep.png")))

    def on_key_down(self):
        self.deck_controller.screen_saver.show()

class SetBrightness(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.set_default_image(Image.open(os.path.join(self.plugin_base.PATH, "assets", "light.png")))

    def get_config_rows(self) -> list:
        self.brightness_row = Adw.PreferencesRow(title="Brightness:")
        self.brighness_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.brightness_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        self.brightness_box.append(Gtk.Label(label="Brightness", margin_bottom=3))
        self.brightness_box.append(self.brighness_scale)

        self.load_config_defaults()

        self.brighness_scale.connect("value-changed", self.on_change_brightness)

        return [self.brightness_row]
    
    def load_config_defaults(self):
        settings = self.get_settings()
        brightness = settings.setdefault("brightness", self.deck_controller.current_brightness)
        self.brighness_scale.set_value(brightness)
        self.set_settings(settings)

    def on_change_brightness(self, scale, *args):
        settings = self.get_settings()
        settings["brightness"] = scale.get_value()
        self.set_settings(settings)

    def on_key_down(self):
        if self.plugin_base.original_brightness is None:
            self.plugin_base.original_brightness = self.deck_controller.current_brightness
        self.deck_controller.set_brightness(self.get_settings().get("brightness", self.deck_controller.current_brightness))

class RevertBrightness(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.set_default_image(Image.open(os.path.join(self.plugin_base.PATH, "assets", "light.png")))

    def on_key_down(self):
        self.deck_controller.set_brightness(self.plugin_base.original_brightness)

class IncreaseBrightness(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.set_default_image(Image.open(os.path.join(self.plugin_base.PATH, "assets", "increase_brightness.png")))

    def on_key_down(self):
        if self.plugin_base.original_brightness is None:
            self.plugin_base.original_brightness = self.deck_controller.current_brightness
        self.deck_controller.set_brightness(self.deck_controller.current_brightness + 10)

class DecreaseBrightness(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.set_default_image(Image.open(os.path.join(self.plugin_base.PATH, "assets", "decrease_brightness.png")))

    def on_key_down(self):
        if self.plugin_base.original_brightness is None:
            self.plugin_base.original_brightness = self.deck_controller.current_brightness
        self.deck_controller.set_brightness(self.deck_controller.current_brightness - 10)

class DeckPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self.original_brightness = None

        self.init_locale_manager()

        ## Register actions
        self.change_page_holder = ActionHolder(
            plugin_base=self,
            action_base=ChangePage,
            action_id="dev_core447_DeckPlugin::ChangePage",
            action_name=self.lm.get("actions.change-page.name")
        )
        self.add_action_holder(self.change_page_holder)

        self.go_to_sleep_holder = ActionHolder(
            plugin_base=self,
            action_base=GoToSleep,
            action_id="dev_core447_DeckPlugin::GoToSleep",
            action_name=self.lm.get("actions.go-to-sleep.name")
        )
        self.add_action_holder(self.go_to_sleep_holder)

        self.change_brightness_holder = ActionHolder(
            plugin_base=self,
            action_base=SetBrightness,
            action_id="dev_core447_DeckPlugin::ChangeBrightness",
            action_name=self.lm.get("actions.set-brightness.name")
        )

        self.revert_brightness_holder = ActionHolder(
            plugin_base=self,
            action_base=RevertBrightness,
            action_id="dev_core447_DeckPlugin::RevertBrightness",
            action_name=self.lm.get("actions.revert-brightness.name")
        )
        self.add_action_holder(self.revert_brightness_holder)

        self.increase_brightness_holder = ActionHolder(
            plugin_base=self,
            action_base=IncreaseBrightness,
            action_id="dev_core447_DeckPlugin::IncreaseBrightness",
            action_name=self.lm.get("actions.increase-brightness.name")
        )
        self.add_action_holder(self.increase_brightness_holder)

        self.decrease_brightness_holder = ActionHolder(
            plugin_base=self,
            action_base=DecreaseBrightness,
            action_id="dev_core447_DeckPlugin::DecreaseBrightness",
            action_name=self.lm.get("actions.decrease-brightness.name")
        )
        self.add_action_holder(self.decrease_brightness_holder)

        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/Core447/DeckPlugin",
            version="0.1"
        )

    def init_locale_manager(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()