# window.py
#
# Copyright 2023 Emmett de St. Croix
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk, GLib, Gio, GObject
import gi
import threading
from .library import AlbumItem, ArtistItem, ArtistList, AlbumList
from .musicdb import MusicDB
from .parser import MusicParser
from .play_queue import PlayQueue
from .player import Player
from .main_view import MainView

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')


@Gtk.Template(resource_path='/com/github/edestcroix/RecordBox/window.ui')
class RecordBoxWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'RecordBoxWindow'

    # outer_split is the AdwOverlaySplitView with the artist/album lists as it's sidebar
    outer_split = Gtk.Template.Child()
    # inner_split is the AdwNavigationSplitView that contains the artist and album lists
    inner_split = Gtk.Template.Child()

    artist_return = Gtk.Template.Child()
    album_return = Gtk.Template.Child()

    artist_list = Gtk.Template.Child()
    album_list = Gtk.Template.Child()
    album_list_page = Gtk.Template.Child()

    progress_bar = Gtk.Template.Child()

    main_page = Gtk.Template.Child()
    main_view = Gtk.Template.Child()

    breakpoint2 = Gtk.Template.Child()

    play_button = Gtk.Template.Child()

    lists_toggle = Gtk.Template.Child()
    queue_toggle = Gtk.Template.Child()

    show_all_artists = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = kwargs.get('application', None)

        self.parser = MusicParser()

        if self.app.settings.get_boolean('restore-window-state'):
            self._bind_state()
        self._bind_settings()
        self._setup_actions()

        self.connect(
            'notify::show-all-artists', lambda *_: self.refresh_lists()
        )

        if self.app.settings.get_boolean('sync-on-startup'):
            self.sync_library(None)

        self.refresh_lists()

    def _bind_state(self):
        self._bind('width', self, 'default-width')
        self._bind('height', self, 'default-height')
        self._bind('is-maximized', self, 'maximized')
        self._bind('is-fullscreen', self, 'fullscreened')

    def _bind_settings(self):
        self._set('artist-sort', self.artist_list, 'sort')
        self._set('album-sort', self.album_list, 'sort')

        self._bind('clear-queue', self.main_view, 'clear_queue')
        self._bind(
            'expand-discs', self.main_view.album_overview, 'expand_discs'
        )

        self._bind('confirm-play', self.main_view, 'confirm_play')

        self._bind('show-all-artists', self, 'show_all_artists')

    def _bind(self, key: str, obj: GObject.Object, property: str):
        self.app.settings.bind(
            key, obj, property, Gio.SettingsBindFlags.DEFAULT
        )

    def _set(self, key: str, obj: GObject.Object, property: str):
        obj.set_property(property, self.app.settings.get_value(key).unpack())

    def _setup_actions(self):
        self.play_action = self._create_action(
            'play-album', self.main_view.play_album
        )
        self.queue_add = self._create_action(
            'add-album', self.main_view.queue_add
        )
        self.replace_queue = self._create_action(
            'replace-queue', self.main_view.replace_queue
        )
        self.return_to_playing = self._create_action(
            'return-to-playing', self.main_view.return_to_playing
        )
        self.undo_queue = self._create_action(
            'undo-queue', self.main_view.undo, enabled=True
        )

        self.filter_all_albums = self._create_action(
            'filter-all', self.filter_all
        )
        self.artist_sort = Gio.PropertyAction.new(
            'artist-sort',
            self.artist_list,
            'sort',
        )
        self.add_action(self.artist_sort)

        self.album_sort = Gio.PropertyAction.new(
            'album-sort',
            self.album_list,
            'sort',
        )
        self.add_action(self.album_sort)

        self.main_view.player.connect(
            'state-changed',
            self._on_player_state_changed,
        )

        self.main_view.player_controls.connect(
            'exit-player',
            self._exit_player,
        )

        self.parser.bind_property(
            'progress',
            self.progress_bar,
            'fraction',
            GObject.BindingFlags.DEFAULT,
        )

    def _create_action(self, name, callback, enabled=False):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        action.set_enabled(enabled)
        self.add_action(action)
        return action

    def sync_library(self, _):
        self.thread = threading.Thread(target=self.update_db)
        self.thread.daemon = True
        self.progress_bar.set_visible(True)
        self.thread.start()

    def update_db(self):
        db = MusicDB()
        self.parser.build(db)
        db.close()
        GLib.idle_add(self.refresh_lists)
        GLib.idle_add(self.progress_bar.set_visible, False)

    def refresh_lists(self):
        db = MusicDB()
        self.artist_list.populate(db.get_artists(self.show_all_artists))
        self.album_list.populate(db.get_albums())
        db.close()

    def filter_all(self, *_):
        self.album_list.filter_all()
        self.filter_all_albums.set_enabled(False)
        self.album_list_page.set_title('Albums')
        self.artist_list.unselect_all()

    @Gtk.Template.Callback()
    def select_album(self, _, album: AlbumItem):
        self.main_view.update_album(album)
        self.main_page.set_title(album.raw_name)
        self.outer_split.set_show_sidebar(
            self.outer_split.get_collapsed() == False
        )

        self.play_button.set_sensitive(True)
        self.play_action.set_enabled(True)
        self.queue_add.set_enabled(True)

    @Gtk.Template.Callback()
    def select_artist(self, _, selected: ArtistItem):
        self.album_list.filter_on_artist(selected.raw_name)
        self.album_list_page.set_title(selected.raw_name)
        self.filter_all_albums.set_enabled(True)
        self.inner_split.set_show_content('album_view')

    @Gtk.Template.Callback()
    def _on_artist_return(self, _):
        self.inner_split.set_show_content('album_view')

    @Gtk.Template.Callback()
    def _on_album_return(self, _):
        self.outer_split.set_show_sidebar(False)

    @Gtk.Template.Callback()
    def _on_album_changed(self, _, album_name: str):
        album = self.album_list.find_album(album_name)

        self.album_list.filter_on_artist(album.artists[0])
        self.album_list_page.set_title(album.artists[0])
        self.main_page.set_title(album.raw_name)
        self.inner_split.set_show_content('album_view')
        self.album_return.set_sensitive(True)

        self.main_view.update_album(album)

        self.album_list.unselect_all()
        self.artist_list.unselect_all()

        self._select_row_with_title(self.artist_list, album.artists[0])
        self._select_row_with_title(self.album_list, album.name)

    @Gtk.Template.Callback()
    def _on_album_activated(self, *_):
        # album row activation only happens on double-click, and the row
        # gets selected on the first click, setting the main_view's album,
        # so we can just call the play_album callback.
        self.main_view.play_album()

    def _select_row_with_title(
        self, row_list: AlbumList | ArtistList, title: str
    ):
        i = 0
        cur = row_list.get_row_at_index(i)
        while cur and cur.raw_name != title:
            i += 1
            cur = row_list.get_row_at_index(i)
        if cur:
            row_list.scroll_to(i, Gtk.ListScrollFlags.SELECT)

    def _on_player_state_changed(self, _, state):
        self.set_hide_on_close(
            self.app.settings.get_boolean('background-playback')
            and state in ['playing', 'paused']
        )
        if state != 'stopped':
            self.replace_queue.set_enabled(True)
            self.queue_toggle.set_sensitive(True)
            self.return_to_playing.set_enabled(True)

    def _exit_player(self, *_):
        self.return_to_playing.set_enabled(False)
        self.queue_toggle.set_sensitive(False)
        self.replace_queue.set_enabled(False)
