#!/usr/bin/env python3
"""
YouTube Music Playlist Merger - Modern GUI Edition v2.1
Dark theme with consistent colors and enhanced features
"""

import os
import sys
import time
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any, Callable
from enum import Enum
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QPropertyAnimation, 
    QEasingCurve, QTimer, QSize, QRect, QObject
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QListWidget, QListWidgetItem, QPlainTextEdit,
    QProgressBar, QComboBox, QMessageBox, QGroupBox, QSpacerItem, QSizePolicy,
    QScrollArea, QDialog, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QGraphicsDropShadowEffect, QStackedWidget, QToolButton, QButtonGroup,
    QRadioButton, QFileDialog, QSplitter, QTextEdit, QDialogButtonBox
)
from PySide6.QtGui import (
    QFont, QFontDatabase, QPalette, QColor, QIcon, 
    QPixmap, QPainter, QBrush, QLinearGradient, QTextCursor
)

try:
    from ytmusicapi import YTMusic
    import ytmusicapi
except ImportError:
    print("Error: ytmusicapi is not installed. Run: pip install ytmusicapi")
    sys.exit(1)

# ============= Constants =============
APP_TITLE = "YouTube Music Playlist Merger"
APP_VERSION = "2.1"
DEFAULT_DEST = "My Merged Playlist"
PRIVACY_CHOICES = ["PRIVATE", "UNLISTED", "PUBLIC"]

APP_DIR = Path(sys.argv[0]).parent.absolute()
SETTINGS_FILE = APP_DIR / "settings.json"

# ============= Logging Setup =============
class LogHandler(logging.Handler, QObject):
    """Custom log handler that emits Qt signals"""
    log_signal = Signal(str, str)  # message, level
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        
    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg, record.levelname)

# Setup logger
logger = logging.getLogger('YTMerger')
logger.setLevel(logging.DEBUG)
log_handler = LogHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                           datefmt='%H:%M:%S'))
logger.addHandler(log_handler)

# ============= Color Scheme (Dark Theme) =============
class ColorScheme:
    PRIMARY = "#1DB954"
    PRIMARY_DARK = "#1AA34A"
    SECONDARY = "#191414"
    BACKGROUND = "#121212"
    SURFACE = "#282828"
    SURFACE_LIGHT = "#3E3E3E"
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#B3B3B3"
    ERROR = "#E22134"
    WARNING = "#FFA500"
    SUCCESS = "#1DB954"
    INFO = "#4FC3F7"

# ============= Custom Widgets =============

class ModernButton(QPushButton):
    """Modern styled button with hover effects"""
    def __init__(self, text="", primary=False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setup_style()
        
    def setup_style(self):
        if self.primary:
            style = f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {ColorScheme.PRIMARY}, stop: 1 {ColorScheme.PRIMARY_DARK});
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {ColorScheme.PRIMARY_DARK}, stop: 1 {ColorScheme.PRIMARY});
            }}
            QPushButton:pressed {{
                background: {ColorScheme.PRIMARY_DARK};
            }}
            QPushButton:disabled {{
                background: {ColorScheme.SURFACE_LIGHT};
                color: {ColorScheme.TEXT_SECONDARY};
            }}
            """
        else:
            style = f"""
            QPushButton {{
                background: {ColorScheme.SURFACE};
                color: {ColorScheme.TEXT_PRIMARY};
                border: 2px solid {ColorScheme.SURFACE_LIGHT};
                padding: 8px 20px;
                border-radius: 18px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {ColorScheme.SURFACE_LIGHT};
                border: 2px solid {ColorScheme.PRIMARY};
            }}
            QPushButton:pressed {{
                background: {ColorScheme.SECONDARY};
            }}
            QPushButton:disabled {{
                background: {ColorScheme.SURFACE};
                color: {ColorScheme.TEXT_SECONDARY};
                border: 2px solid {ColorScheme.SURFACE};
            }}
            """
        self.setStyleSheet(style)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

class ModernCard(QFrame):
    """Card-like container with shadow"""
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title_label = None
        self.setup_ui(title)
        
    def setup_ui(self, title):
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(f"""
            QFrame {{
                background: {ColorScheme.SURFACE};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
        
        self.layout = QVBoxLayout(self)
        
        if title:
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {ColorScheme.TEXT_PRIMARY};
                padding-bottom: 12px;
            """)
            self.layout.addWidget(self.title_label)

class LogViewer(QWidget):
    """Android logcat-style log viewer"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with toggle button
        header = QHBoxLayout()
        
        self.toggle_btn = QPushButton("📋 Logs")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)
        self.toggle_btn.clicked.connect(self.toggle_visibility)
        header.addWidget(self.toggle_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_logs)
        header.addWidget(self.clear_btn)
        
        header.addStretch()
        
        # Log level filter
        header.addWidget(QLabel("Filter:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        header.addWidget(self.level_combo)
        
        layout.addLayout(header)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setVisible(False)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background: {ColorScheme.SECONDARY};
                color: {ColorScheme.TEXT_PRIMARY};
                border: 1px solid {ColorScheme.SURFACE_LIGHT};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
        """)
        
        layout.addWidget(self.log_text)
        
    def toggle_visibility(self):
        self.log_text.setVisible(self.toggle_btn.isChecked())
        
    def add_log(self, message: str, level: str):
        colors = {
            "DEBUG": "#888888",
            "INFO": ColorScheme.INFO,
            "WARNING": ColorScheme.WARNING,
            "ERROR": ColorScheme.ERROR
        }
        color = colors.get(level, ColorScheme.TEXT_PRIMARY)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f'<span style="color: {color}">[{timestamp}] [{level}] {message}</span><br>'
        
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(formatted)
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
        
    def clear_logs(self):
        self.log_text.clear()
        
    def filter_logs(self):
        # This would filter existing logs - simplified for this example
        pass

# ============= Preview Dialog =============

class PreviewDialog(QDialog):
    """Preview dialog showing merge details"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Merge Preview")
        self.setMinimumSize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        # Statistics card
        stats_card = ModernCard("Statistics")
        self.stats_layout = QVBoxLayout()
        stats_card.layout.addLayout(self.stats_layout)
        layout.addWidget(stats_card)
        
        # Tab widget for tracks
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ColorScheme.SURFACE_LIGHT};
                background: {ColorScheme.SURFACE};
            }}
            QTabBar::tab {{
                background: {ColorScheme.SURFACE};
                color: {ColorScheme.TEXT_PRIMARY};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {ColorScheme.PRIMARY};
                color: white;
            }}
        """)
        
        # To Add tab
        self.add_table = self.create_track_table()
        self.tabs.addTab(self.add_table, "Tracks to Add")
        
        # Skipped tab
        self.skip_table = self.create_track_table(include_reason=True)
        self.tabs.addTab(self.skip_table, "Skipped Tracks")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def create_track_table(self, include_reason=False):
        table = QTableWidget()
        
        headers = ["Title", "Artists", "Duration", "Source"]
        if include_reason:
            headers.append("Reason")
            
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {ColorScheme.BACKGROUND};
                color: {ColorScheme.TEXT_PRIMARY};
                gridline-color: {ColorScheme.SURFACE_LIGHT};
            }}
            QHeaderView::section {{
                background: {ColorScheme.SURFACE};
                color: {ColorScheme.TEXT_PRIMARY};
                padding: 8px;
                border: none;
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background: {ColorScheme.PRIMARY};
            }}
        """)
        
        return table
        
    def set_statistics(self, stats: Dict):
        # Clear existing stats
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Add statistics
        for key, value in stats.items():
            label = QLabel(f"<b>{key}:</b> {value}")
            label.setStyleSheet(f"color: {ColorScheme.TEXT_PRIMARY}; padding: 2px;")
            self.stats_layout.addWidget(label)
            
    def populate_tables(self, to_add: List, skipped: List):
        # Populate "to add" table
        self.add_table.setRowCount(len(to_add))
        for i, track in enumerate(to_add):
            self.add_table.setItem(i, 0, QTableWidgetItem(track.get("title", "")))
            self.add_table.setItem(i, 1, QTableWidgetItem(track.get("artists", "")))
            self.add_table.setItem(i, 2, QTableWidgetItem(track.get("duration", "")))
            self.add_table.setItem(i, 3, QTableWidgetItem(track.get("source", "")))
            
        # Update tab title
        self.tabs.setTabText(0, f"Tracks to Add ({len(to_add)})")
        
        # Populate skipped table
        self.skip_table.setRowCount(len(skipped))
        for i, track in enumerate(skipped):
            self.skip_table.setItem(i, 0, QTableWidgetItem(track.get("title", "")))
            self.skip_table.setItem(i, 1, QTableWidgetItem(track.get("artists", "")))
            self.skip_table.setItem(i, 2, QTableWidgetItem(track.get("duration", "")))
            self.skip_table.setItem(i, 3, QTableWidgetItem(track.get("source", "")))
            self.skip_table.setItem(i, 4, QTableWidgetItem(track.get("reason", "")))
            
        # Update tab title
        self.tabs.setTabText(1, f"Skipped Tracks ({len(skipped)})")

# ============= Data Models =============

class AppSettings:
    """Application settings manager"""
    def __init__(self):
        self.settings = self.load_settings()
    
    def load_settings(self) -> dict:
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_dest_title": DEFAULT_DEST,
            "last_privacy": "PRIVATE",
            "include_liked": False,
            "browser_file": None
        }
    
    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

# ============= Helper Functions =============

def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds to readable string"""
    if seconds is None:
        return "—"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def track_video_id(track: Dict) -> Optional[str]:
    """Extract video ID from track data"""
    return track.get("videoId") or track.get("setVideoId")

def get_artist_text(track: Dict) -> str:
    """Extract artist text from track data"""
    if isinstance(track.get("artists"), list) and track["artists"]:
        names = [a.get("name") for a in track["artists"] if a.get("name")]
        return ", ".join(names) if names else ""
    return str(track.get("author", track.get("artistsText", "")))

def get_duration_text(track: Dict) -> str:
    """Extract duration text from track data"""
    for key in ("duration", "length", "lengthText"):
        if val := track.get(key):
            return str(val)
    
    if "lengthSeconds" in track:
        try:
            return format_duration(int(track["lengthSeconds"]))
        except:
            pass
    
    return "—"

# ============= Worker Threads =============

class PreviewWorker(QThread):
    """Worker for generating merge preview"""
    status = Signal(str)
    done = Signal(bool, str, dict)
    
    def __init__(self, auth_path: str, sources: List[Dict], 
                 dest_title: str, include_liked: bool):
        super().__init__()
        self.auth_path = auth_path
        self.sources = sources
        self.dest_title = dest_title
        self.include_liked = include_liked
        
    def run(self):
        try:
            from ytmusicapi import YTMusic
            yt = YTMusic(self.auth_path)
            
            logger.info(f"Generating preview for {len(self.sources)} playlists")
            
            # Get destination playlist if it exists
            dest_id = None
            dest_existing_ids = set()
            
            self.status.emit("Checking destination playlist...")
            playlists = yt.get_library_playlists(limit=10000)
            
            for p in playlists:
                if p.get("title", "").strip().lower() == self.dest_title.strip().lower():
                    dest_id = p.get("playlistId")
                    break
                    
            if dest_id:
                self.status.emit("Reading existing tracks in destination...")
                logger.info(f"Found existing destination playlist: {dest_id}")
                try:
                    if dest_id == "LM":
                        dest_tracks = yt.get_liked_songs(limit=100000).get("tracks", [])
                    else:
                        wp = yt.get_watch_playlist(playlistId=dest_id, limit=10000)
                        dest_tracks = wp.get("tracks", [])
                    dest_existing_ids = {track_video_id(t) for t in dest_tracks if track_video_id(t)}
                    logger.info(f"Destination has {len(dest_existing_ids)} existing tracks")
                except Exception as e:
                    logger.warning(f"Failed to get destination tracks: {e}")
                    
            # Collect all tracks
            to_add = []
            skipped = []
            seen_ids = set()
            total_tracks = 0
            
            # Process each source
            for source in self.sources:
                self.status.emit(f"Processing: {source['title']}")
                logger.info(f"Processing playlist: {source['title']}")
                
                try:
                    if source["playlistId"] == "LM":
                        tracks = yt.get_liked_songs(limit=100000).get("tracks", [])
                    else:
                        wp = yt.get_watch_playlist(playlistId=source["playlistId"], limit=10000)
                        tracks = wp.get("tracks", [])
                        
                    logger.info(f"Found {len(tracks)} tracks in {source['title']}")
                    
                    for track in tracks:
                        total_tracks += 1
                        vid = track_video_id(track)
                        
                        track_info = {
                            "title": track.get("title", "Unknown"),
                            "artists": get_artist_text(track),
                            "duration": get_duration_text(track),
                            "source": source["title"],
                            "video_id": vid
                        }
                        
                        if not vid:
                            track_info["reason"] = "No video ID"
                            skipped.append(track_info)
                        elif vid in dest_existing_ids:
                            track_info["reason"] = "Already in destination"
                            skipped.append(track_info)
                        elif vid in seen_ids:
                            track_info["reason"] = "Duplicate"
                            skipped.append(track_info)
                        else:
                            to_add.append(track_info)
                            seen_ids.add(vid)
                            
                except Exception as e:
                    logger.error(f"Failed to process {source['title']}: {e}")
                    
            # Process liked songs if requested
            if self.include_liked:
                self.status.emit("Processing liked songs...")
                logger.info("Processing liked songs")
                try:
                    tracks = yt.get_liked_songs(limit=100000).get("tracks", [])
                    logger.info(f"Found {len(tracks)} liked songs")
                    
                    for track in tracks:
                        total_tracks += 1
                        vid = track_video_id(track)
                        
                        track_info = {
                            "title": track.get("title", "Unknown"),
                            "artists": get_artist_text(track),
                            "duration": get_duration_text(track),
                            "source": "Liked Songs",
                            "video_id": vid
                        }
                        
                        if not vid:
                            track_info["reason"] = "No video ID"
                            skipped.append(track_info)
                        elif vid in dest_existing_ids:
                            track_info["reason"] = "Already in destination"
                            skipped.append(track_info)
                        elif vid in seen_ids:
                            track_info["reason"] = "Duplicate"
                            skipped.append(track_info)
                        else:
                            to_add.append(track_info)
                            seen_ids.add(vid)
                except Exception as e:
                    logger.error(f"Failed to process liked songs: {e}")
                    
            # Prepare statistics
            stats = {
                "Total tracks processed": total_tracks,
                "Tracks to add": len(to_add),
                "Tracks skipped": len(skipped),
                "Already in destination": sum(1 for t in skipped if t["reason"] == "Already in destination"),
                "Duplicates removed": sum(1 for t in skipped if t["reason"] == "Duplicate"),
                "No video ID": sum(1 for t in skipped if t["reason"] == "No video ID"),
                "Destination exists": "Yes" if dest_id else "No (will be created)"
            }
            
            result = {
                "to_add": to_add,
                "skipped": skipped,
                "stats": stats
            }
            
            logger.info(f"Preview complete: {len(to_add)} to add, {len(skipped)} skipped")
            self.done.emit(True, "Preview generated successfully", result)
            
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            self.done.emit(False, f"Failed to generate preview: {str(e)}", {})

class PublishWorker(QThread):
    """Worker for publishing the merge"""
    status = Signal(str)
    progress = Signal(int)
    done = Signal(bool, str, str)
    
    def __init__(self, auth_path: str, video_ids: List[str], 
                 dest_title: str, privacy: str, description: str = ""):
        super().__init__()
        self.auth_path = auth_path
        self.video_ids = video_ids
        self.dest_title = dest_title
        self.privacy = privacy
        self.description = description or "Auto-merged playlist from YouTube Music"
        
    def run(self):
        try:
            from ytmusicapi import YTMusic
            yt = YTMusic(self.auth_path)
            
            logger.info(f"Publishing {len(self.video_ids)} tracks to {self.dest_title}")
            
            # Find or create destination
            self.status.emit("Finding destination playlist...")
            playlists = yt.get_library_playlists(limit=10000)
            dest_id = None
            
            for p in playlists:
                if p.get("title", "").strip().lower() == self.dest_title.strip().lower():
                    dest_id = p.get("playlistId")
                    logger.info(f"Found existing playlist: {dest_id}")
                    break
                    
            if not dest_id:
                self.status.emit(f"Creating new playlist: {self.dest_title}")
                dest_id = yt.create_playlist(
                    self.dest_title, self.description, privacy_status=self.privacy
                )
                logger.info(f"Created new playlist: {dest_id}")
                
            # Add tracks in batches
            if self.video_ids:
                batch_size = 50
                total_batches = (len(self.video_ids) + batch_size - 1) // batch_size
                
                for i in range(0, len(self.video_ids), batch_size):
                    batch = self.video_ids[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    self.status.emit(f"Adding batch {batch_num}/{total_batches}...")
                    yt.add_playlist_items(dest_id, batch, duplicates=False)
                    
                    progress = int((i + len(batch)) * 100 / len(self.video_ids))
                    self.progress.emit(progress)
                    
                    logger.info(f"Added batch {batch_num}/{total_batches} ({len(batch)} tracks)")
                    
            playlist_url = f"https://music.youtube.com/playlist?list={dest_id}"
            logger.info(f"Successfully published playlist: {playlist_url}")
            self.done.emit(True, f"Successfully added {len(self.video_ids)} tracks!", playlist_url)
            
        except Exception as e:
            logger.error(f"Publishing failed: {e}")
            self.done.emit(False, f"Publishing failed: {str(e)}", "")

# ============= Main Window =============

class ModernMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.auth_verified = False
        self.library_playlists = []
        self.browser_file_path = None
        self.preview_data = None
        
        self.init_ui()
        self.apply_theme()
        self.load_saved_settings()
        
        # Connect log handler
        log_handler.log_signal.connect(self.log_viewer.add_log)
        
        logger.info("Application started")
        
    def init_ui(self):
        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION}")
        self.setMinimumSize(1200, 900)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Content area with cards
        content = QWidget()
        content.setStyleSheet(f"background: {ColorScheme.BACKGROUND};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Step 1: Authentication Card
        auth_card = self.create_auth_card()
        content_layout.addWidget(auth_card)
        
        # Step 2: Playlist Selection Card
        playlist_card = self.create_playlist_card()
        content_layout.addWidget(playlist_card)
        
        # Step 3: Action Card
        action_card = self.create_action_card()
        content_layout.addWidget(action_card)
        
        # Progress and Status
        progress_widget = self.create_progress_widget()
        content_layout.addWidget(progress_widget)
        
        content_layout.addStretch()
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {ColorScheme.SURFACE};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {ColorScheme.PRIMARY};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)
        
        splitter.addWidget(scroll)
        
        # Log viewer at bottom
        self.log_viewer = LogViewer()
        splitter.addWidget(self.log_viewer)
        
        # Set splitter sizes (80% content, 20% logs when visible)
        splitter.setSizes([800, 200])
        
        main_layout.addWidget(splitter)
        
    def create_header(self):
        """Create application header"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {ColorScheme.PRIMARY}, stop: 1 {ColorScheme.PRIMARY_DARK});
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 30, 0)
        
        # Title
        title = QLabel(APP_TITLE)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
        """)
        layout.addWidget(title)
        
        # Version badge
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet("""
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        """)
        layout.addWidget(version)
        
        layout.addStretch()
        
        return header
    
    def create_auth_card(self):
        """Create authentication card"""
        auth_card = ModernCard("Step 1: Authentication")
        
        # Status indicator
        self.auth_status = QLabel("Not Authenticated")
        self.update_auth_status(False)
        auth_card.layout.addWidget(self.auth_status)
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.auth_file_label = QLabel("No file selected")
        self.auth_file_label.setStyleSheet(f"color: {ColorScheme.TEXT_SECONDARY};")
        file_layout.addWidget(self.auth_file_label, 1)
        
        self.browse_btn = ModernButton("Browse", primary=False)
        self.browse_btn.clicked.connect(self.browse_auth_file)
        file_layout.addWidget(self.browse_btn)
        
        auth_card.layout.addLayout(file_layout)
        
        # Test button
        self.test_auth_btn = ModernButton("Test Authentication", primary=True)
        self.test_auth_btn.clicked.connect(self.test_authentication)
        self.test_auth_btn.setEnabled(False)
        auth_card.layout.addWidget(self.test_auth_btn)
        
        # Instructions (collapsible)
        instructions_btn = QPushButton("📖 Show Instructions")
        instructions_btn.setCheckable(True)
        instructions_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ColorScheme.PRIMARY};
                border: none;
                text-align: left;
                padding: 5px;
            }}
        """)
        
        instructions = QLabel(
            "<b>Create browser.json (Firefox):</b><br>"
            "1) Go to <b>music.youtube.com</b> and log in to your account<br>"
            "2) Press <b>F12</b> to open Developer Tools → Go to <b>Network</b> tab<br>"
            "3) <b>Disable cache</b> (checkbox in Network tab)<br>"
            "4) Click on <b>Library</b> in YouTube Music, then <b>reload the page</b><br>"
            "5) In Network tab, filter by <b>XHR</b> and search for '<b>/browse</b>'<br>"
            "6) Click on '<b>browse?prettyPrint=false</b>' request<br>"
            "7) Go to <b>Request Headers</b> → Switch to <b>Raw</b> view<br>"
            "8) <b>Copy all</b> the raw headers text<br>"
            "9) Open terminal/command prompt and run: <b>ytmusicapi browser</b><br>"
            "10) <b>Paste</b> the headers → Press <b>Enter</b><br>"
            "11) Press <b>Ctrl+Z</b> (Windows) or <b>Ctrl+D</b> (macOS/Linux) → <b>Enter</b><br>"
            "12) This creates <b>browser.json</b> - Browse and select it above"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"""
            color: {ColorScheme.TEXT_SECONDARY};
            padding: 10px;
            background: {ColorScheme.BACKGROUND};
            border-radius: 8px;
        """)
        instructions.setVisible(False)
        
        instructions_btn.toggled.connect(lambda checked: instructions.setVisible(checked))
        instructions_btn.toggled.connect(lambda checked: instructions_btn.setText(
            "📖 Hide Instructions" if checked else "📖 Show Instructions"
        ))
        
        auth_card.layout.addWidget(instructions_btn)
        auth_card.layout.addWidget(instructions)
        
        return auth_card
    
    def create_playlist_card(self):
        """Create playlist selection card"""
        playlist_card = ModernCard("Step 2: Select Playlists")
        
        # Load button and filter
        controls = QHBoxLayout()
        
        self.load_btn = ModernButton("Load Playlists", primary=True)
        self.load_btn.clicked.connect(self.load_playlists)
        self.load_btn.setEnabled(False)
        controls.addWidget(self.load_btn)
        
        controls.addWidget(QLabel("Filter:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Type to filter...")
        self.filter_input.setStyleSheet(f"""
            QLineEdit {{
                background: {ColorScheme.BACKGROUND};
                border: 2px solid {ColorScheme.SURFACE_LIGHT};
                border-radius: 8px;
                padding: 8px;
                color: {ColorScheme.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 2px solid {ColorScheme.PRIMARY};
            }}
        """)
        self.filter_input.textChanged.connect(self.filter_playlists)
        controls.addWidget(self.filter_input, 1)
        
        self.select_all_btn = ModernButton("Select All")
        self.select_all_btn.clicked.connect(lambda: self.set_all_selected(True))
        controls.addWidget(self.select_all_btn)
        
        self.select_none_btn = ModernButton("Select None")
        self.select_none_btn.clicked.connect(lambda: self.set_all_selected(False))
        controls.addWidget(self.select_none_btn)
        
        playlist_card.layout.addLayout(controls)
        
        # Include liked songs
        self.include_liked = QCheckBox("Include Liked Songs")
        self.include_liked.setStyleSheet(f"""
            QCheckBox {{
                color: {ColorScheme.TEXT_PRIMARY};
                padding: 5px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
            }}
        """)
        playlist_card.layout.addWidget(self.include_liked)
        
        # Playlist list
        self.playlist_list = QListWidget()
        self.playlist_list.setStyleSheet(f"""
            QListWidget {{
                background: {ColorScheme.BACKGROUND};
                border: none;
                border-radius: 8px;
                padding: 10px;
            }}
            QListWidget::item {{
                background: {ColorScheme.SURFACE};
                color: {ColorScheme.TEXT_PRIMARY};
                padding: 10px;
                margin: 2px;
                border-radius: 6px;
            }}
            QListWidget::item:hover {{
                background: {ColorScheme.SURFACE_LIGHT};
            }}
            QListWidget::item:selected {{
                background: {ColorScheme.PRIMARY};
            }}
        """)
        self.playlist_list.setMinimumHeight(300)
        playlist_card.layout.addWidget(self.playlist_list)
        
        # Destination settings
        dest_layout = QHBoxLayout()
        
        dest_layout.addWidget(QLabel("Destination Name:"))
        self.dest_input = QLineEdit(self.settings.get("last_dest_title", DEFAULT_DEST))
        self.dest_input.setStyleSheet(f"""
            QLineEdit {{
                background: {ColorScheme.BACKGROUND};
                border: 2px solid {ColorScheme.SURFACE_LIGHT};
                border-radius: 8px;
                padding: 8px;
                color: {ColorScheme.TEXT_PRIMARY};
            }}
        """)
        dest_layout.addWidget(self.dest_input, 1)
        
        dest_layout.addWidget(QLabel("Privacy:"))
        self.privacy_combo = QComboBox()
        self.privacy_combo.addItems(PRIVACY_CHOICES)
        self.privacy_combo.setCurrentText(self.settings.get("last_privacy", "PRIVATE"))
        self.privacy_combo.setMinimumWidth(150)  # Make sure full text is visible
        self.privacy_combo.setStyleSheet(f"""
            QComboBox {{
                background: {ColorScheme.SURFACE};
                border: 2px solid {ColorScheme.SURFACE_LIGHT};
                border-radius: 8px;
                padding: 8px;
                color: {ColorScheme.TEXT_PRIMARY};
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {ColorScheme.TEXT_SECONDARY};
            }}
            QComboBox QAbstractItemView {{
                background: {ColorScheme.SURFACE};
                color: {ColorScheme.TEXT_PRIMARY};
                selection-background-color: {ColorScheme.PRIMARY};
                border: 1px solid {ColorScheme.SURFACE_LIGHT};
            }}
        """)
        dest_layout.addWidget(self.privacy_combo)
        
        playlist_card.layout.addLayout(dest_layout)
        
        return playlist_card
    
    def create_action_card(self):
        """Create action buttons card"""
        action_card = ModernCard("Step 3: Preview & Publish")
        
        button_layout = QHBoxLayout()
        
        self.preview_btn = ModernButton("Preview Changes", primary=False)
        self.preview_btn.clicked.connect(self.preview_merge)
        self.preview_btn.setEnabled(False)
        button_layout.addWidget(self.preview_btn)
        
        self.publish_btn = ModernButton("Publish Playlist", primary=True)
        self.publish_btn.clicked.connect(self.publish_playlist)
        self.publish_btn.setEnabled(False)
        button_layout.addWidget(self.publish_btn)
        
        button_layout.addStretch()
        
        action_card.layout.addLayout(button_layout)
        
        # Result link
        self.result_label = QLabel()
        self.result_label.setOpenExternalLinks(True)
        self.result_label.setStyleSheet(f"color: {ColorScheme.PRIMARY};")
        action_card.layout.addWidget(self.result_label)
        
        return action_card
    
    def create_progress_widget(self):
        """Create progress indicator widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
            color: {ColorScheme.TEXT_SECONDARY};
            font-size: 14px;
            padding: 5px;
        """)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {ColorScheme.SURFACE};
                border-radius: 10px;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {ColorScheme.PRIMARY}, stop: 1 {ColorScheme.PRIMARY_DARK});
                border-radius: 10px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        return widget
    
    def update_auth_status(self, authenticated: bool):
        """Update authentication status display"""
        if authenticated:
            self.auth_status.setText("✓ Authenticated")
            self.auth_status.setStyleSheet(f"""
                background: {ColorScheme.SUCCESS};
                color: white;
                padding: 8px 16px;
                border-radius: 16px;
                font-weight: bold;
            """)
        else:
            self.auth_status.setText("✗ Not Authenticated")
            self.auth_status.setStyleSheet(f"""
                background: {ColorScheme.ERROR};
                color: white;
                padding: 8px 16px;
                border-radius: 16px;
                font-weight: bold;
            """)
    
    def apply_theme(self):
        """Apply dark theme"""
        self.setStyleSheet(f"""
            QWidget {{
                background: {ColorScheme.BACKGROUND};
                color: {ColorScheme.TEXT_PRIMARY};
            }}
            QMessageBox {{
                background: {ColorScheme.SURFACE};
            }}
        """)
        
        logger.info("Applied dark theme")
    
    def load_saved_settings(self):
        """Load saved user settings"""
        self.dest_input.setText(self.settings.get("last_dest_title", DEFAULT_DEST))
        self.privacy_combo.setCurrentText(self.settings.get("last_privacy", "PRIVATE"))
        self.include_liked.setChecked(self.settings.get("include_liked", False))
        
        # Load saved browser file
        if browser_file := self.settings.get("browser_file"):
            if Path(browser_file).exists():
                self.browser_file_path = browser_file
                self.auth_file_label.setText(f"Selected: {Path(browser_file).name}")
                self.test_auth_btn.setEnabled(True)
                logger.info(f"Loaded saved browser file: {browser_file}")
    
    def save_current_settings(self):
        """Save current user settings"""
        self.settings.set("last_dest_title", self.dest_input.text())
        self.settings.set("last_privacy", self.privacy_combo.currentText())
        self.settings.set("include_liked", self.include_liked.isChecked())
        if self.browser_file_path:
            self.settings.set("browser_file", self.browser_file_path)
    
    @Slot()
    def browse_auth_file(self):
        """Browse for browser.json file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select browser.json file",
            str(APP_DIR),
            "JSON Files (*.json)"
        )
        
        if file_path:
            self.browser_file_path = file_path
            self.auth_file_label.setText(f"Selected: {Path(file_path).name}")
            self.test_auth_btn.setEnabled(True)
            self.settings.set("browser_file", file_path)
            logger.info(f"Selected browser file: {file_path}")
    
    @Slot()
    def test_authentication(self):
        """Test authentication with browser.json"""
        if not self.browser_file_path:
            QMessageBox.warning(self, "No File", "Please select browser.json first")
            return
        
        self.status_label.setText("Testing authentication...")
        self.progress_bar.setRange(0, 0)
        
        logger.info("Testing authentication...")
        
        from threading import Thread
        
        def test():
            try:
                yt = YTMusic(self.browser_file_path)
                playlists = yt.get_library_playlists(limit=1)
                version = getattr(ytmusicapi, '__version__', 'unknown')
                self.on_auth_test_done(True, f"Authentication successful! (ytmusicapi v{version})")
            except Exception as e:
                self.on_auth_test_done(False, f"Authentication failed: {str(e)}")
        
        Thread(target=test, daemon=True).start()
    
    def on_auth_test_done(self, success: bool, message: str):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            self.auth_verified = True
            self.update_auth_status(True)
            self.load_btn.setEnabled(True)
            self.status_label.setText(message)
            logger.info("Authentication successful")
        else:
            self.update_auth_status(False)
            QMessageBox.critical(self, "Authentication Failed", message)
            self.status_label.setText("Authentication failed")
            logger.error(f"Authentication failed: {message}")
    
    @Slot()
    def load_playlists(self):
        """Load user's playlists"""
        self.status_label.setText("Loading playlists...")
        self.progress_bar.setRange(0, 0)
        
        logger.info("Loading playlists...")
        
        from threading import Thread
        
        def load():
            try:
                yt = YTMusic(self.browser_file_path)
                playlists = yt.get_library_playlists(limit=10000)
                self.on_playlists_loaded(True, f"Loaded {len(playlists)} playlists", playlists)
            except Exception as e:
                self.on_playlists_loaded(False, f"Failed to load library: {str(e)}", [])
        
        Thread(target=load, daemon=True).start()
    
    def on_playlists_loaded(self, success: bool, message: str, playlists: list):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            self.library_playlists = playlists
            self.playlist_list.clear()
            
            for playlist in playlists:
                title = playlist.get("title", "Untitled")
                playlist_id = playlist.get("playlistId")
                
                if playlist_id:
                    item = QListWidgetItem(title)
                    item.setData(Qt.UserRole, playlist_id)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    self.playlist_list.addItem(item)
            
            self.status_label.setText(f"Loaded {len(playlists)} playlists")
            self.preview_btn.setEnabled(True)
            logger.info(f"Successfully loaded {len(playlists)} playlists")
        else:
            QMessageBox.critical(self, "Load Failed", message)
            self.status_label.setText("Failed to load playlists")
            logger.error(f"Failed to load playlists: {message}")
    
    @Slot()
    def filter_playlists(self):
        """Filter playlist list based on search text"""
        search_text = self.filter_input.text().lower()
        
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            item.setHidden(search_text not in item.text().lower())
    
    def set_all_selected(self, selected: bool):
        """Select or deselect all playlists"""
        state = Qt.Checked if selected else Qt.Unchecked
        
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            if not item.isHidden():
                item.setCheckState(state)
    
    def get_selected_playlists(self) -> List[Dict]:
        """Get list of selected playlists"""
        selected = []
        dest_title = self.dest_input.text().strip().lower()
        
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            if item.checkState() == Qt.Checked:
                playlist_id = item.data(Qt.UserRole)
                title = item.text()
                
                if title.lower() != dest_title:
                    selected.append({
                        "title": title,
                        "playlistId": playlist_id
                    })
        
        return selected
    
    @Slot()
    def preview_merge(self):
        """Preview the merge operation"""
        selected = self.get_selected_playlists()
        
        if not selected and not self.include_liked.isChecked():
            QMessageBox.information(self, "No Selection", 
                                   "Please select at least one playlist")
            return
        
        self.status_label.setText("Generating preview...")
        self.progress_bar.setRange(0, 0)
        
        logger.info("Generating merge preview...")
        
        self.preview_worker = PreviewWorker(
            self.browser_file_path,
            selected,
            self.dest_input.text(),
            self.include_liked.isChecked()
        )
        self.preview_worker.status.connect(lambda msg: self.status_label.setText(msg))
        self.preview_worker.done.connect(self.on_preview_done)
        self.preview_worker.start()
    
    @Slot(bool, str, dict)
    def on_preview_done(self, success: bool, message: str, data: dict):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            self.preview_data = data
            self.status_label.setText("Preview generated")
            
            # Show preview dialog
            dialog = PreviewDialog(self)
            dialog.set_statistics(data["stats"])
            dialog.populate_tables(data["to_add"], data["skipped"])
            
            if dialog.exec() == QDialog.Accepted:
                self.publish_btn.setEnabled(True)
                logger.info("Preview accepted, ready to publish")
            
        else:
            QMessageBox.critical(self, "Preview Failed", message)
            self.status_label.setText("Preview failed")
            logger.error(f"Preview failed: {message}")
    
    @Slot()
    def publish_playlist(self):
        """Publish the merged playlist"""
        if not self.preview_data:
            QMessageBox.warning(self, "No Preview", 
                               "Please preview changes first")
            return
        
        video_ids = [t["video_id"] for t in self.preview_data["to_add"] if t.get("video_id")]
        
        if not video_ids:
            QMessageBox.information(self, "Nothing to Add", 
                                   "No tracks to add to playlist")
            return
        
        self.save_current_settings()
        
        self.status_label.setText("Publishing playlist...")
        self.progress_bar.setValue(0)
        self.result_label.clear()
        
        logger.info(f"Publishing {len(video_ids)} tracks...")
        
        self.publish_worker = PublishWorker(
            self.browser_file_path,
            video_ids,
            self.dest_input.text(),
            self.privacy_combo.currentText()
        )
        self.publish_worker.status.connect(lambda msg: self.status_label.setText(msg))
        self.publish_worker.progress.connect(self.progress_bar.setValue)
        self.publish_worker.done.connect(self.on_publish_done)
        self.publish_worker.start()
    
    @Slot(bool, str, str)
    def on_publish_done(self, success: bool, message: str, playlist_url: str):
        if success:
            self.status_label.setText(message)
            self.progress_bar.setValue(100)
            
            if playlist_url:
                self.result_label.setText(
                    f'<a href="{playlist_url}" style="color: {ColorScheme.PRIMARY};">Open Merged Playlist</a>'
                )
            
            QMessageBox.information(self, "Success", message)
            logger.info(f"Successfully published playlist: {playlist_url}")
        else:
            self.status_label.setText("Publishing failed")
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "Publishing Failed", message)
            logger.error(f"Publishing failed: {message}")

# ============= Main Entry Point =============

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = ModernMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()