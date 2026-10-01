import os
import sys
import time
import ctypes
from PyQt5.QtCore import QObject, QProcess, QThread, QSharedMemory, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction

from ui import theme
from brand import APP_ID, APP_FULL, APP_NAME, SINGLETON_KEY, TRAY_MENU_EXIT, TRAY_MENU_OPEN, TRAY_MENU_SETTINGS, TRAY_TOOLTIP

ICON_PATH = os.path.join('assets', 'ghosttype.ico')

from key_listener import KeyListener
from result_thread import ResultThread
from ui.dashboard_window import DashboardWindow
from ui.status_window import StatusWindow
from transcription import create_local_model
from input_simulation import InputSimulator
from history import HistoryStore
from sound import play_completion_sound
from utils import ConfigManager


class ModelLoadThread(QThread):
    """Loads (or reloads) the local Whisper model off the UI thread."""
    loaded = pyqtSignal(object)

    def run(self):
        try:
            model = create_local_model()
        except Exception as e:
            ConfigManager.console_print(f'Model load failed: {e}')
            model = None
        self.loaded.emit(model)


class WhisperWriterApp(QObject):
    def __init__(self, preloaded_model=None):
        """``preloaded_model`` is the WhisperModel run.py loaded BEFORE PyQt5 was
        imported (see run.py:_preload_whisper_model — the ctranslate2/PyQt5 DLL
        conflict makes a post-Qt load segfault). None means the preload failed or
        API mode is on; we fall back to loading lazily off the UI thread."""
        super().__init__()
        # HiDPI: Qt5 needs to be told explicitly, or on a 4K/150%-scaled display
        # every widget renders at 1x physical pixels and the UI looks tiny.
        # Must be set BEFORE the QApplication below is constructed.
        try:
            from PyQt5.QtCore import Qt
            from PyQt5.QtWidgets import QApplication
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except Exception as e:
            print(f'[ghosttype] WARNING: HiDPI attributes not set: {e}', flush=True)
        # Make Windows treat this as its own app (own taskbar icon, not pythonw's).
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            pass

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName(APP_NAME)
        self._app_icon = QIcon(ICON_PATH)
        self.app.setWindowIcon(self._app_icon)

        # Base font. Qt's inherited default here is 8pt "MS Shell Dlg 2", which on a
        # 4K/200%-scaled display renders far too small to read. HiDPI scaling alone
        # does NOT fix this — it scales whatever size it is handed. The dashboard
        # creates ~45 widgets with only one explicit setFont(), so the app-wide font
        # is what almost every label, button and dropdown inherits. Set it once here.
        base_font = QFont('Segoe UI', 10)
        base_font.setHintingPreference(QFont.PreferFullHinting)
        self.app.setFont(base_font)

        # Single-instance guard: if another copy is already running, bail out so we
        # don't get two key listeners typing the same text twice.
        self._shared = QSharedMemory(SINGLETON_KEY)
        if not self._shared.create(1):
            print('ghosttype is already running. Exiting this instance.')
            sys.exit(0)

        ConfigManager.initialize()
        theme.set_theme(ConfigManager.get_config_value('misc', 'theme') or 'dark')
        self.history = HistoryStore()

        self._rec_start = 0.0
        self._rec_duration = 0.0
        self._reinsert_text = ''
        self.model_loader = None
        self._cur_device = None
        self._cur_compute = None

        # Stash the preloaded model for initialize_components() to pick up.
        self._preloaded_model = preloaded_model

        self.initialize_components()

    def initialize_components(self):
        """Initialize the components of the application."""
        self.input_simulator = InputSimulator()

        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.on_activation)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)

        model_options = ConfigManager.get_config_section('model_options')
        self._cur_device = ConfigManager.get_config_value('model_options', 'local', 'device')
        self._cur_compute = ConfigManager.get_config_value('model_options', 'local', 'compute_type')
        # Model is loaded in run.py BEFORE PyQt5 imports (DLL conflict avoidance),
        # and handed to us via the constructor. If the preload failed (or API mode
        # is on) we retry once off the UI thread so the dashboard isn't blocked.
        if model_options.get('use_api'):
            self.local_model = None
        elif self._preloaded_model is not None:
            self.local_model = self._preloaded_model
            print('[ghosttype] Using model preloaded before Qt init.', flush=True)
        else:
            self.local_model = None
            self.model_loader = ModelLoadThread()
            self.model_loader.loaded.connect(self._on_model_loaded)
            self.model_loader.start()

        self.result_thread = None
        self.target_window = None

        self.dashboard = DashboardWindow(self.history)
        self.dashboard.setWindowIcon(self._app_icon)
        self._connect_dashboard()

        if not ConfigManager.get_config_value('misc', 'hide_status_window'):
            self.status_window = StatusWindow()
            self.status_window.setWindowIcon(self._app_icon)
        else:
            self.status_window = None

        self.create_tray_icon()
        self.key_listener.start()
        # Default to tray-only. The dashboard is ~940x660, which is roughly a
        # third of a 1600x1000 screen — showing it on every launch is what made
        # the app feel like it was taking over the desktop. It is still one
        # tray click (or double-click the tray icon) away.
        if not ConfigManager.get_config_value('misc', 'start_minimized'):
            self.dashboard.show()

    def _connect_dashboard(self):
        self.dashboard.recordToggle.connect(self.on_activation)
        self.dashboard.modelChanged.connect(self.change_model)
        self.dashboard.settingsSaved.connect(self.apply_settings)
        self.dashboard.reinsertRequested.connect(self.on_reinsert)

    def create_tray_icon(self):
        """Create the system tray icon and its context menu."""
        self.tray_icon = QSystemTrayIcon(self._app_icon, self.app)
        self.tray_icon.setToolTip(TRAY_TOOLTIP)

        tray_menu = QMenu()

        show_action = QAction(TRAY_MENU_OPEN, self.app)
        show_action.triggered.connect(self.show_dashboard)
        tray_menu.addAction(show_action)

        settings_action = QAction(TRAY_MENU_SETTINGS, self.app)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        exit_action = QAction(TRAY_MENU_EXIT, self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_dashboard()

    def show_dashboard(self):
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def open_settings(self):
        self.dashboard.open_settings()

    def on_reinsert(self, text):
        """Type a history entry into whatever window is focused after we hid ours."""
        self._reinsert_text = text
        QTimer.singleShot(350, self._do_reinsert)

    def _do_reinsert(self):
        if not self._reinsert_text:
            return
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        self.input_simulator.typewrite(self._reinsert_text, hwnd)
        self._reinsert_text = ''

    def apply_settings(self):
        """Apply saved settings live, without restarting the app."""
        # Theme change → rebuild the dashboard with the new palette.
        new_theme = ConfigManager.get_config_value('misc', 'theme') or 'dark'
        if new_theme != getattr(theme, 'ACTIVE', 'dark'):
            theme.set_theme(new_theme)
            self._rebuild_dashboard()

        # Hotkey / mode / backend → reload the key listener.
        try:
            self.key_listener.stop()
            self.key_listener.update_activation_keys()
            self.key_listener.start()
        except Exception as e:
            ConfigManager.console_print(f'Key listener reload failed: {e}')

        # Status window visibility.
        hide = ConfigManager.get_config_value('misc', 'hide_status_window')
        if hide and self.status_window:
            self.status_window = None
        elif not hide and not self.status_window:
            self.status_window = StatusWindow()
            self.status_window.setWindowIcon(self._app_icon)

        # Reload the model only if device/compute type changed (expensive).
        dev = ConfigManager.get_config_value('model_options', 'local', 'device')
        ct = ConfigManager.get_config_value('model_options', 'local', 'compute_type')
        if (dev, ct) != (self._cur_device, self._cur_compute):
            self._cur_device, self._cur_compute = dev, ct
            self.dashboard.set_status('loading')
            self.model_loader = ModelLoadThread()
            self.model_loader.loaded.connect(self._on_model_loaded)
            self.model_loader.start()

    def _rebuild_dashboard(self):
        """Recreate the dashboard window (used when the theme changes)."""
        old = self.dashboard
        was_visible = old.isVisible()
        geo = old.geometry()
        self.dashboard = DashboardWindow(self.history)
        self.dashboard.setWindowIcon(self._app_icon)
        self.dashboard.setGeometry(geo)
        self._connect_dashboard()
        old.hide()
        old.deleteLater()
        if was_visible:
            self.dashboard.open_settings()

    def change_model(self, name, path):
        """Switch the active local model (loaded off the UI thread)."""
        if ConfigManager.get_config_value('model_options', 'local', 'model') == name and \
           ConfigManager.get_config_value('model_options', 'local', 'model_path') == path:
            return
        ConfigManager.set_config_value(name, 'model_options', 'local', 'model')
        # Empty path => model isn't installed yet; clear model_path so faster-whisper
        # downloads it by name (otherwise it would keep loading the previous model).
        ConfigManager.set_config_value(path or '', 'model_options', 'local', 'model_path')
        ConfigManager.save_config()

        self.dashboard.set_status('loading')
        self.model_loader = ModelLoadThread()
        self.model_loader.loaded.connect(self._on_model_loaded)
        self.model_loader.start()

    def _on_model_loaded(self, model):
        if model is not None:
            self.local_model = model
            self.dashboard.set_status('idle')
            # A freshly downloaded model is now installed — refresh the picker marks.
            self.dashboard._sync_model_combo()
        else:
            self.dashboard.set_status('error')

    def cleanup(self):
        if getattr(self, 'key_listener', None):
            self.key_listener.stop()
        if getattr(self, 'input_simulator', None):
            self.input_simulator.cleanup()
        # Release the single-instance lock so a restart can re-acquire it.
        if getattr(self, '_shared', None) and self._shared.isAttached():
            self._shared.detach()

    def exit_app(self):
        """Exit the application."""
        self.cleanup()
        self.tray_icon.hide()
        QApplication.quit()

    def restart_app(self):
        """Restart the application to apply the new settings."""
        self.cleanup()
        self.tray_icon.hide()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def on_activation(self):
        """Called when the activation key combination is pressed."""
        if self.result_thread and self.result_thread.isRunning():
            recording_mode = ConfigManager.get_config_value('recording_options', 'recording_mode')
            if recording_mode == 'press_to_toggle':
                self.result_thread.stop_recording()
            elif recording_mode == 'continuous':
                self.stop_result_thread()
            return

        self.target_window = ctypes.windll.user32.GetForegroundWindow()
        self.start_result_thread()

    def on_deactivation(self):
        """Called when the activation key combination is released."""
        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'hold_to_record':
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()

    def start_result_thread(self):
        """Start the result thread to record audio and transcribe it."""
        if self.result_thread and self.result_thread.isRunning():
            return

        if self.local_model is None:
            self.dashboard.set_status('error')
            ConfigManager.console_print(
                'No local model loaded — transcription would fail. '
                'Pick a model in Settings to (re)load it.')
            return

        self.result_thread = ResultThread(self.local_model)
        self.result_thread.statusSignal.connect(self.on_status_update)
        if self.status_window:
            self.result_thread.statusSignal.connect(self.status_window.updateStatus)
            self.result_thread.audioLevelSignal.connect(self.status_window.updateAudioLevel)
            self.status_window.closeSignal.connect(self.stop_result_thread)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.start()

    def stop_result_thread(self):
        """Stop the result thread."""
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()

    def on_status_update(self, status):
        """Reflect recording status in the dashboard and measure duration."""
        if status == 'recording':
            self._rec_start = time.time()
        elif status == 'transcribing':
            self._rec_duration = time.time() - self._rec_start
        self.dashboard.set_status(status)

    def on_transcription_complete(self, result):
        """When transcription is complete, save it, type it, and resume listening."""
        if result:
            model_name = ConfigManager.get_config_value('model_options', 'local', 'model') or ''
            self.history.add(result, self._rec_duration, model_name)
            if self.dashboard.isVisible():
                self.dashboard.refresh_history()

        self.input_simulator.typewrite(result, self.target_window)
        self.target_window = None

        # Brief "Typed" acknowledgement in the indicator — the only feedback that
        # matters for a hands-free flow: you need to know the text actually landed
        # in the app you were talking to, without looking away from it.
        if self.status_window and not self.dashboard.isVisible():
            self.status_window.show_typed(result)

        if ConfigManager.get_config_value('misc', 'noise_on_completion'):
            play_completion_sound()

        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'continuous':
            self.start_result_thread()
        else:
            self.key_listener.start()

    def run(self):
        """Start the application."""
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    # Only reached if someone runs `python src/main.py` directly. Normal launches
    # go through run.py, which MUST own startup: it scrubs PYTHONPATH, fixes the
    # CUDA DLL order, and preloads the model BEFORE PyQt5 imports (a load after Qt
    # segfaults on the ctranslate2/PyQt5 DLL conflict). Running main.py alone skips
    # all of that, so warn rather than pretend it's equivalent.
    print('[ghosttype] WARNING: run via run.py, not main.py — model preload order '
          'is required to avoid the ctranslate2/PyQt5 segfault.', flush=True)
    app = WhisperWriterApp()
    app.run()
