from gi.repository import Adw, Gtk, GLib, Gio, GObject
import gi

gi.require_version('Gtk', '4.0')


@Gtk.Template(resource_path='/com/github/edestcroix/RecordBox/preferences.ui')
class RecordBoxPreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'RecordBoxPreferencesWindow'

    clear_queue = Gtk.Template.Child()
    background_playback = Gtk.Template.Child()
    expand_discs = Gtk.Template.Child()
    artist_sort = Gtk.Template.Child()
    album_sort = Gtk.Template.Child()
    show_all_artists = Gtk.Template.Child()
    restore_window_state = Gtk.Template.Child()
    restore_playback_state = Gtk.Template.Child()
    sync_on_startup = Gtk.Template.Child()

    rg_mode = Gtk.Template.Child()
    rg_enable = Gtk.Template.Child()
    rg_preamp = Gtk.Template.Child()
    rg_fallback = Gtk.Template.Child()

    directory_select_button = Gtk.Template.Child()
    music_directory = GObject.Property(type=str, default='')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.artist_sort.connect('notify::selected', self._artist_out)
        self.album_sort.connect('notify::selected', self._album_out)
        self.rg_mode.connect('notify::selected', self._rg_mode_out)

    def bind_settings(self, settings: Gio.Settings):
        self.settings = settings
        self._artist_in()
        self._album_in()
        self._rg_mode_in()

        self._bind('music-directory', self, 'music-directory')

        self.settings.connect('changed::artist-sort', self._artist_in)
        self.settings.connect('changed::album-sort', self._album_in)
        self.settings.connect('changed::rg-mode', self._rg_mode_in)

        self._bind('clear-queue', self.clear_queue, 'active')

        self._bind('background-playback', self.background_playback, 'active')

        self._bind('expand-discs', self.expand_discs, 'active')

        self._bind('show-all-artists', self.show_all_artists, 'active')

        self._bind('restore-window-state', self.restore_window_state, 'active')
        self._bind(
            'restore-playback-state', self.restore_playback_state, 'active'
        )

        self._bind('sync-on-startup', self.sync_on_startup, 'active')

        self._bind('rg-enabled', self.rg_enable, 'enable-expansion')
        self._bind('rg-preamp', self.rg_preamp, 'value')
        self._bind('rg-fallback', self.rg_fallback, 'value')

    def _bind(self, key, obj, prop):
        self.settings.bind(key, obj, prop, Gio.SettingsBindFlags.DEFAULT)

    def _artist_out(self, *_):
        self.settings.set_enum('artist-sort', self.artist_sort.get_selected())

    def _artist_in(self, *_):
        self.artist_sort.set_selected(self.settings.get_enum('artist-sort'))

    def _album_out(self, *_):
        self.settings.set_enum('album-sort', self.album_sort.get_selected())

    def _album_in(self, *_):
        self.album_sort.set_selected(self.settings.get_enum('album-sort'))

    def _rg_mode_out(self, *_):
        self.settings.set_enum('rg-mode', self.rg_mode.get_selected())

    def _rg_mode_in(self, *_):
        self.rg_mode.set_selected(self.settings.get_enum('rg-mode'))

    @Gtk.Template.Callback()
    def _on_directory_select_button_clicked(self, _):
        file_chooser = Gtk.FileDialog()
        file_chooser.set_initial_folder(
            Gio.File.new_for_path(GLib.get_home_dir())
        )
        file_chooser.select_folder(callback=self._on_folder_selected)

    def _on_folder_selected(self, dialog, response):
        folder: Gio.LocalFile = dialog.select_folder_finish(response)

        self.music_directory = folder.get_path()
