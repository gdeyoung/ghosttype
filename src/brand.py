"""Centralized branding and user-facing strings for ghosttype.

Single source of truth so future renames or translations touch one file.
Import these constants instead of hardcoding 'WhisperWriter' or Russian text."""

# Application identity (shown in window title, tray tooltip, single-instance key).
APP_NAME = 'ghosttype'
APP_FULL = 'ghosttype — voice typing'  # Used in window titles.

# Windows app-user-model-id (taskbar grouping + own taskbar icon).
APP_ID = 'ghosttype.VoiceTyping'

# Single-instance guard key. Bumping the suffix is a cheap way to invalidate
# any stale running instance from a previous branding.
SINGLETON_KEY = 'ghosttype-singleton-v1'

# HKCU Run registry value name (auto-start). Keep stable across releases so
# the entry doesn't accumulate duplicates when ghosttype updates.
AUTOSTART_REGISTRY_NAME = 'ghosttype'

# Tray icon.
TRAY_TOOLTIP = 'ghosttype — press your hotkey to start/stop dictation'

# Tray context menu.
TRAY_MENU_OPEN = 'Open ghosttype'
TRAY_MENU_SETTINGS = 'Settings'
TRAY_MENU_EXIT = 'Exit'

# Dashboard title bar.
DASHBOARD_TITLE = 'ghosttype'
DASHBOARD_BYLINE = 'voice typing'

# Status messages (keyed by state name).
STATUS_READY = 'Ready'
STATUS_LISTENING = 'Listening…'
STATUS_TRANSCRIBING = 'Transcribing…'
STATUS_LOADING = 'Loading model…'
STATUS_ERROR = 'Error'

# Slim floating indicator pill (bottom-centre, never takes focus).
INDICATOR_READY = 'Ready'
INDICATOR_LISTENING = 'Listening'
INDICATOR_TRANSCRIBING = 'Transcribing…'
INDICATOR_TYPED = 'Typed'

STATUS_MAP = {
    'idle': STATUS_READY,
    'recording': STATUS_LISTENING,
    'transcribing': STATUS_TRANSCRIBING,
    'loading': STATUS_LOADING,
    'error': STATUS_ERROR,
}

# Common buttons.
BTN_CANCEL = 'Cancel'
BTN_SAVE = 'Save'
BTN_CLEAR_ALL = 'Clear all'
BTN_RECORD = 'Record  (or hotkey)'
BTN_STOP = 'Stop recording'
BTN_PRESS_KEYS = 'Press keys'
BTN_PREVIEW = '▶ Preview'

# Recording mode dropdown labels (must match schema order: continuous,
# voice_activity_detection, press_to_toggle, hold_to_record).
MODE_CONTINUOUS = 'Continuous'
MODE_VAD = 'On silence (VAD)'
MODE_TOGGLE = 'Press to start / stop'
MODE_HOLD = 'Hold to talk'
MODES = [MODE_CONTINUOUS, MODE_VAD, MODE_TOGGLE, MODE_HOLD]

# Language dropdown (display label, ISO code). Auto-detect is the empty string.
LANG_AUTO_LABEL = 'Auto-detect'
LANG_AUTO_CODE = ''
LANGS = [
    (LANG_AUTO_LABEL, LANG_AUTO_CODE),
    ('English', 'en'), ('Spanish', 'es'), ('Italian', 'it'),
    ('French', 'fr'), ('German', 'de'), ('Portuguese', 'pt'),
    ('Polish', 'pl'), ('Russian', 'ru'), ('Ukrainian', 'uk'),
    ('Chinese', 'zh'), ('Japanese', 'ja'), ('Turkish', 'tr'),
]
LANG_FIELD_LABEL = 'Language'
LANG_FIELD_TOOLTIP = 'Spoken language (or "Auto-detect").'

# Transcription task (transcribe vs translate).
TASK_TRANSCRIBE = 'Transcribe (as spoken)'
TASK_TRANSLATE = 'Translate to English'
TASKS = [(TASK_TRANSCRIBE, 'transcribe'), (TASK_TRANSLATE, 'translate')]
TASK_FIELD_LABEL = 'Recognition mode'
TASK_FIELD_TOOLTIP = 'Translation only outputs English (Whisper limitation).'

# Settings field labels.
RECORDING_MODE_LABEL = 'Recording mode'
DEVICE_LABEL = 'Device'
COMPUTE_TYPE_LABEL = 'Compute type'

# Theme labels (must match schema: dark, light).
THEME_DARK = 'Dark'
THEME_LIGHT = 'Light'
THEMES = [(THEME_DARK, 'dark'), (THEME_LIGHT, 'light')]
THEME_LABEL = 'Theme'

# Replacements field.
REPLACEMENTS_LABEL = 'Text replacements'
REPLACEMENTS_TOOLTIP = 'One per line: "phrase => replacement". Voice commands, punctuation, line breaks (\\n).'

# Post-processing toggles.
POSTPROC_ADD_SPACE = 'Add trailing space'
POSTPROC_CAPITALIZE = 'Capitalize first letter of sentences'
POSTPROC_PLAY_SOUND = 'Play sound on completion'

# Completion sound dropdown (display label, asset path).
SOFT_SOUND = 'Soft'
DING_SOUND = 'Ding'
POP_SOUND = 'Pop'
MARIMBA_SOUND = 'Marimba'
BLIP_SOUND = 'Blip'
BEEP_SOUND = 'Beep (legacy)'
COMPLETION_SOUNDS = [
    (SOFT_SOUND, 'assets/sounds/soft.wav'),
    (DING_SOUND, 'assets/sounds/ding.wav'),
    (POP_SOUND, 'assets/sounds/pop.wav'),
    (MARIMBA_SOUND, 'assets/sounds/marimba.wav'),
    (BLIP_SOUND, 'assets/sounds/blip.wav'),
    (BEEP_SOUND, 'assets/beep.wav'),
]
COMPLETION_SOUND_LABEL = 'Completion sound'
VOLUME_LABEL = 'Volume: {pct}%'

# Misc toggles.
HIDE_STATUS_LABEL = 'Hide floating recording indicator'
AUTOSTART_LABEL = 'Launch at Windows startup'

# Hotkey capture dialog.
HOTKEY_HEADING = 'Set hotkey'
HOTKEY_LABEL = 'Hotkey'
HOTKEY_INSTRUCTION = ("Press the keys you want to combine, e.g. Ctrl + Win, or "
                      "Ctrl + Shift + Space.")
HOTKEY_SAVE_HINT = 'Release the keys, then press Save.'

# Settings panel.
SETTINGS_HEADING = 'Settings'
SETTINGS_NOTE = 'Settings apply immediately — no restart needed.'

# History panel.
HISTORY_HEADING = 'History'
HISTORY_SEARCH_PLACEHOLDER = '🔍  Search transcripts…'
HISTORY_EMPTY = 'No transcriptions yet.'

# Per-entry history actions.
INSERT_TOOLTIP = 'Insert at cursor'
COPY_TOOLTIP = 'Copy to clipboard'
DELETE_TOOLTIP = 'Delete this entry'

# Model field label on the dashboard.
LABEL_MODEL = 'Model'
