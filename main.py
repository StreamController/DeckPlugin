from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

from packaging import version

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


from plugins.com_core447_DeckPlugin.ComboRow import ComboRow


# Import signals
from src.Signals import Signals

class ChangePage(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.HAS_CONFIGURATION = True

        self.connect(signal=Signals.PageRename, callback=self.on_page_rename)
        self.connect(signal=Signals.PageAdd, callback=self.update_available_pages)
        self.connect(signal=Signals.PageDelete, callback=self.update_available_pages)

    def on_ready(self):
        # Ensures that there is always one page selected
        settings = self.get_settings()
        settings.setdefault("selected_page", gl.page_manager.get_pages()[0])
        self.set_settings(settings)
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "folder.png"))

    def get_config_rows(self) -> list:
        ## Page selector
        self.page_model = Gtk.ListStore.new([str, str])
        self.page_selector_row = ComboRow(model=self.page_model, title=self.plugin_base.lm.get("actions.change-page.drop-down-label"))

        self.page_selector_cell_renderer = Gtk.CellRendererText()
        self.page_selector_row.combo_box.pack_start(self.page_selector_cell_renderer, True)
        self.page_selector_row.combo_box.add_attribute(self.page_selector_cell_renderer, "text", 0)

        ## Deck selector
        self.deck_model = Gtk.ListStore.new([str, str])
        self.deck_selector_row = ComboRow(model=self.deck_model, title=self.plugin_base.lm.get("actions.change.page.deck-drop-down-label"))

        self.deck_selector_cell_renderer = Gtk.CellRendererText()
        self.deck_selector_row.combo_box.pack_start(self.deck_selector_cell_renderer, True)
        self.deck_selector_row.combo_box.add_attribute(self.deck_selector_cell_renderer, "text", 0)
        
        self.load_page_model()
        self.load_deck_model()

        self.load_config_defaults()

        self.page_selector_row.combo_box.connect("changed", self.on_page_changed)
        self.deck_selector_row.combo_box.connect("changed", self.on_deck_changed)

        return [self.page_selector_row, self.deck_selector_row]
        

    def load_page_model(self):
        for page in gl.page_manager.get_pages():
            display_name = os.path.splitext(os.path.basename(page))[0]
            self.page_model.append([display_name, page])

    def update_available_pages(self, *args) -> None:
        if not hasattr(self, "page_selector_row"):
            # Skip if not in config area
            return
        
        self.page_selector_row.combo_box.disconnect_by_func(self.on_page_changed)
        
        self.page_model.clear()
        self.load_page_model()

        # Select page
        settings = self.get_settings()
        selected_page = settings.setdefault("selected_page", None)
        self.select_page(selected_page)

        self.page_selector_row.combo_box.connect("changed", self.on_page_changed)

    def load_deck_model(self) -> None:
        for controller in gl.deck_manager.deck_controller:
            deck_number, deck_type = gl.app.main_win.leftArea.deck_stack.get_page_attributes(controller)
            self.deck_model.append([deck_type, deck_number])

    def load_config_defaults(self):
        settings = self.get_settings()
        if settings == None:
            return
        
        # Update page selector
        selected_page = settings.setdefault("selected_page", None)
        self.select_page(selected_page)

        deck_number = settings.setdefault("deck_number", None)
        self.select_deck(deck_number)

    def select_page(self, page_path: str) -> None:
        for i, row in enumerate(self.page_model):
            if row[1] == page_path:
                self.page_selector_row.combo_box.set_active(i)
                return
            
        self.page_selector_row.combo_box.set_active(-1)

    def select_deck(self, deck_number: str) -> None:
        for i, row in enumerate(self.deck_model):
            if row[1] == deck_number:
                self.deck_selector_row.combo_box.set_active(i)
                return
            
        self.deck_selector_row.combo_box.set_active(-1)
        

    def on_page_changed(self, combo, *args):
        page_path = self.page_model[combo.get_active()][1]
        

        settings = self.get_settings()
        settings["selected_page"] = page_path
        self.set_settings(settings)

    def on_deck_changed(self, combo, *args):
        deck_number = self.deck_model[combo.get_active()][1]
        
        settings = self.get_settings()
        settings["deck_number"] = deck_number
        self.set_settings(settings)

    def get_deck_controller_to_use(self) -> DeckController:
        settings = self.get_settings()
        deck_type = settings.get("deck_number")

        # Find controller
        for controller in gl.deck_manager.deck_controller:
            if controller.deck.get_serial_number() == deck_type:
                return controller
            
        # Use own controller as fallback
        return self.deck_controller


    def on_key_down(self):
        page_path = self.get_settings().get("selected_page")
        if page_path is None:
            return
        
        controller = self.get_deck_controller_to_use()

        page = gl.page_manager.get_page(page_path, deck_controller=controller)
        controller.load_page(page)

    def on_page_rename(self, old_path: str, new_path: str):
        settings = self.get_settings()
        set_path = settings.get("selected_page")
        if set_path in [None, ""]:
            return
        if os.path.abspath(set_path) == os.path.abspath(old_path):
            settings["selected_page"] = new_path
            self.set_settings(settings)

            if hasattr(self, "page_model"):
                # Update page model
                self.page_selector_row.combo_box.disconnect_by_func(self.on_page_changed)
                self.page_model.clear()
                self.load_page_model()
                self.select_page(new_path)
                self.page_selector_row.combo_box.connect("changed", self.on_page_changed)

class ChangeState(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.connect(signal=Signals.RemoveState, callback=self.on_state_removed)

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "sidebar.png"), size=0.8)

    def get_config_rows(self) -> list:
        n_states = len(self.get_own_key().states)
        self.spinner = Adw.SpinRow.new_with_range(1, n_states, 1)
        self.spinner.set_snap_to_ticks(True)
        self.spinner.set_title("State:")

        self.load_config_defaults()

        self.spinner.connect("changed", self.on_change_state)

        return [self.spinner]
    
    def load_config_defaults(self):
        settings = self.get_settings()
        state = settings.setdefault("state", 0)
        self.spinner.set_value(state + 1)
    
    def on_change_state(self, spinner):
        settings = self.get_settings()
        settings["state"] = round(spinner.get_value()) - 1
        self.set_settings(settings)

    def on_key_down(self):
        state = self.get_settings().get("state")
        if state == self.state:
            return
        self.get_own_key().set_state(state)

    def on_state_removed(self, state, state_map):
        settings = self.get_settings()
        set_state = settings.get("state")
        if state == set_state:
            settings["state"] = self.state
        else:
            settings["state"] = state_map.get(set_state, self.state)

        self.set_settings(settings)

class GoToSleep(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "sleep.png"), size=0.8)

    def on_key_down(self):
        self.deck_controller.screen_saver.show()

class SetBrightness(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.HAS_CONFIGURATION = True

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "light.png"))

    def get_config_rows(self) -> list:
        self.brightness_row = Adw.PreferencesRow(title="Brightness:")
        self.brighness_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.brighness_scale.set_draw_value(True)
        self.brightness_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True,
                                      margin_top=5, margin_bottom=5, margin_start=5, margin_end=5)
        self.brightness_box.append(Gtk.Label(label=self.plugin_base.lm.get("actions.set-brightness.scale-label"), margin_bottom=5, xalign=0))
        self.brightness_box.append(self.brighness_scale)
        self.brightness_row.set_child(self.brightness_box)

        self.load_config_defaults()

        self.brighness_scale.connect("value-changed", self.on_change_brightness)

        return [self.brightness_row]
    
    def load_config_defaults(self):
        settings = self.get_settings()
        brightness = settings.setdefault("brightness", self.deck_controller.brightness)
        self.brighness_scale.set_value(brightness)
        self.set_settings(settings)

    def on_change_brightness(self, scale, *args):
        settings = self.get_settings()
        settings["brightness"] = scale.get_value()
        self.set_settings(settings)

    def on_key_down(self):
        if self.plugin_base.original_brightness is None:
            self.plugin_base.original_brightness = self.deck_controller.brightness
        self.deck_controller.set_brightness(self.get_settings().get("brightness", self.deck_controller.brightness))

class RevertBrightness(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "light.png"))

    def on_key_down(self):
        self.deck_controller.set_brightness(self.plugin_base.original_brightness)

class IncreaseBrightness(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "increase_brightness.png"))

    def on_key_down(self):
        if self.plugin_base.original_brightness is None:
            self.plugin_base.original_brightness = self.deck_controller.brightness
        self.deck_controller.set_brightness(min(100, self.deck_controller.brightness + 10))

class DecreaseBrightness(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "decrease_brightness.png"))

    def on_key_down(self):
        if self.plugin_base.original_brightness is None:
            self.plugin_base.original_brightness = self.deck_controller.brightness
        self.deck_controller.set_brightness(max(0, self.deck_controller.brightness - 10))

class DeckPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self.original_brightness = None

        self.init_locale_manager()

        ## Register actions
        self.change_page_holder = ActionHolder(
            plugin_base=self,
            action_base=ChangePage,
            action_id="com_core447_DeckPlugin::ChangePage",
            action_name=self.lm.get("actions.change-page.name")
        )
        self.add_action_holder(self.change_page_holder)

        self.go_to_sleep_holder = ActionHolder(
            plugin_base=self,
            action_base=GoToSleep,
            action_id="com_core447_DeckPlugin::GoToSleep",
            action_name=self.lm.get("actions.go-to-sleep.name")
        )
        self.add_action_holder(self.go_to_sleep_holder)

        self.change_brightness_holder = ActionHolder(
            plugin_base=self,
            action_base=SetBrightness,
            action_id="com_core447_DeckPlugin::ChangeBrightness",
            action_name=self.lm.get("actions.set-brightness.name")
        )
        self.add_action_holder(self.change_brightness_holder)

        self.revert_brightness_holder = ActionHolder(
            plugin_base=self,
            action_base=RevertBrightness,
            action_id="com_core447_DeckPlugin::RevertBrightness",
            action_name=self.lm.get("actions.revert-brightness.name")
        )
        self.add_action_holder(self.revert_brightness_holder)

        self.increase_brightness_holder = ActionHolder(
            plugin_base=self,
            action_base=IncreaseBrightness,
            action_id="com_core447_DeckPlugin::IncreaseBrightness",
            action_name=self.lm.get("actions.increase-brightness.name")
        )
        self.add_action_holder(self.increase_brightness_holder)

        self.decrease_brightness_holder = ActionHolder(
            plugin_base=self,
            action_base=DecreaseBrightness,
            action_id="com_core447_DeckPlugin::DecreaseBrightness",
            action_name=self.lm.get("actions.decrease-brightness.name")
        )
        self.add_action_holder(self.decrease_brightness_holder)

        if version.parse(gl.app_version) >= version.parse("1.5.1-beta"): # backward compatibility
            self.change_state_holder = ActionHolder(
                plugin_base=self,
                action_base=ChangeState,
                min_app_version="1.5.1-beta",
                action_id="com_core447_DeckPlugin::ChangeState",
                action_name="Change State"
            )
            self.add_action_holder(self.change_state_holder)

        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/StreamController/DeckPlugin",
            plugin_version="1.0.0",
            app_version="1.0.0-alpha"
        )

    def init_locale_manager(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()