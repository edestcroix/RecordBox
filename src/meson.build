
python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)
conf.set('APP_ID', application_id)

configure_file(
  input: 'recordbox.in',
  output: 'recordbox',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr--r--'
)

recordbox_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'library.py',
  'library_lists.py',
  'items.py',
  'album_view.py',
  'player_controls.py',
  'play_queue.py',
  'preferences.py',
  'player.py',
  'musicdb.py',
  'parser.py',
  'mpris.py',
]



install_data(recordbox_sources, install_dir: moduledir)
