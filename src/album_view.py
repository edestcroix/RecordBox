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

from gi.repository import Adw, Gtk, GLib, GObject, Gdk
import gi

gi.require_version('Gtk', '4.0')

from .musicdb import MusicDB, Album


@Gtk.Template(resource_path='/com/github/edestcroix/RecordBox/album_view.ui')
class RecordBoxAlbumView(Adw.Bin):
    __gtype_name__ = 'RecordBoxAlbumView'

    cover_image = Gtk.Template.Child()

    track_list = Gtk.Template.Child()

    album_box = Gtk.Template.Child()

    stack = Gtk.Template.Child()
    current_album = None

    _expand_discs = False

    @GObject.Property(type=bool, default=False)
    def expand_discs(self):
        return self._collapse_discs

    @expand_discs.setter
    def set_expand_discs(self, value):
        self._collapse_discs = value

    @GObject.Signal(
        arg_types=(GObject.TYPE_PYOBJECT,), return_type=GObject.TYPE_NONE
    )
    def play_track(self, _):
        pass

    @GObject.Signal(
        arg_types=(GObject.TYPE_PYOBJECT,), return_type=GObject.TYPE_NONE
    )
    def add_track(self, _):
        pass

    def set_breakpoint(self, _):
        self.album_box.set_orientation(Gtk.Orientation.VERTICAL)

    def unset_breakpoint(self, _):
        self.album_box.set_orientation(Gtk.Orientation.HORIZONTAL)

    def update_cover(self, cover_path):
        self.cover_image.set_from_file(cover_path)

    def clear_all(self):
        self.track_list.remove_all()

    def update_album(self, album: Album, current_artist=None):
        self.current_album = album
        self.clear_all()
        self.update_cover(album.cover)
        self.update_tracks(album.get_tracks(), current_artist)
        self.stack.set_visible_child_name('album_view')

    def update_tracks(self, tracks, current_artist):
        current_disc, disc_row = 0, None
        for track in tracks:
            if track.disc_num() != current_disc:
                disc_row = self._disc_row(current_disc := track.disc_num())
            self._setup_row(track, disc_row, current_artist)

    def _disc_row(self, current_disc):
        disc_row = Adw.ExpanderRow(
            title=f'Disc {current_disc}',
            selectable=False,
            expanded=self.expand_discs,
        )
        self.track_list.append(disc_row)
        return disc_row

    def _setup_row(self, track, disc_row, current_artist):
        row = self._create_row(track, current_artist)
        row.connect('play_track', lambda *_: self.emit('play_track', track))
        row.connect('add_track', lambda *_: self.emit('add_track', track))
        if disc_row:
            disc_row.add_row(row)
        else:
            self.track_list.append(row)

    def _create_row(self, track, current_artist, parent_row=None):
        row = TrackRow(track=track, current_artist=current_artist)
        row.set_title_lines(1)
        row.set_selectable(False)
        if parent_row:
            row.get_style_context().add_class('property')
            parent_row.add_row(row)
        return row


class TrackRow(Adw.ActionRow):
    def __init__(self, track, current_artist, **kwargs):
        super().__init__(**kwargs)
        self.track = track
        track_num = track.track_num()
        self.set_title_lines(1)
        self.set_title(GLib.markup_escape_text(track.title))

        if track.albumartist != current_artist:
            artists = f"\n{', '.join([track.albumartist] + track.artists)}"
        elif artists := track.artists:
            artists = f"\n{', '.join(artists)}"
        else:
            artists = ''
        self.set_subtitle(
            GLib.markup_escape_text(
                f'{track_num:0>2} - {track.length_str()}{artists}'
            )
        )
        self.set_tooltip_text(track.title)
        btn = self._create_button(
            'view-more-symbolic', lambda _: self.popover.popup()
        )
        self.popover = self._create_popover(btn)
        self.add_suffix(btn)

    @GObject.Signal(
        arg_types=(GObject.TYPE_PYOBJECT,), return_type=GObject.TYPE_NONE
    )
    def play_track(self, _):
        pass

    @GObject.Signal(
        arg_types=(GObject.TYPE_PYOBJECT,), return_type=GObject.TYPE_NONE
    )
    def add_track(self, _):
        pass

    def sort_key(self):
        return (self.track.disc_num(), self.track.track_num())

    def _create_button(self, icon_name, callback, title=None, args=None):
        if title:
            button, content = Gtk.Button(), Adw.ButtonContent()
            content.set_label(title)
            content.set_icon_name(icon_name)
            button.set_child(content)
        else:
            button = Gtk.Button.new_from_icon_name(icon_name)
        button.set_css_classes(['flat'])
        button.set_valign(Gtk.Align.CENTER)
        if args:
            button.connect('clicked', callback, args)
        else:
            button.connect('clicked', callback)
        return button

    def _create_popover(self, parent):
        popover = Gtk.Popover.new()
        popover.set_parent(parent)
        popover.set_position(Gtk.PositionType.BOTTOM)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(
            self._create_button(
                'media-playback-start-symbolic',
                self._popover_selected,
                'Play track',
                'play_track',
            )
        )
        box.append(
            self._create_button(
                'list-add-symbolic',
                self._popover_selected,
                'Add to queue',
                'add_track',
            )
        )
        popover.set_child(box)
        popover.present()
        return popover

    def _popover_selected(self, _, action):
        self.popover.popdown()
        self.emit(action, self.track)
