import sys
import requests
import json
import threading
import time
import anthropic
import openai
from collections import defaultdict
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QComboBox, QLabel,
    QSplitter, QProgressBar, QTabWidget, QDialog, QDialogButtonBox, QToolBar, QAction, QSpinBox, QMessageBox, QCheckBox, QSizePolicy, QScrollArea, QGridLayout
)
from PyQt5.QtGui import QColor, QTextCursor, QFont, QTextCharFormat, QPainter, QSyntaxHighlighter, QLinearGradient, QPalette, QBrush
from PyQt5.QtCore import Qt, pyqtSlot, Q_ARG, QMetaObject, pyqtSignal, QTimer, QSize, QThread, QRect
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis, QLineSeries
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from bs4 import BeautifulSoup

class Theme:
    DARK = {
        'bg': '#1e1e2e',
        'text': '#cdd6f4',
        'button': '#45475a',
        'button_hover': '#585b70',
        'input': '#313244',
        'border': '#6c7086',
        'scroll_bg': '#313244',
        'scroll_handle': '#585b70',
        'status_bg': '#313244',
        'status_chunk': '#89b4fa',
        'accent': '#cba6f7'
    }

class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Segoe UI", 10))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton:pressed {
                background-color: #313244;
            }
            QPushButton:disabled {
                background-color: #313244;
                color: #6c7086;
            }
        """)

class ModernComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #6c7086;
                padding: 5px;
                border-radius: 8px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #6c7086;
                border-left-style: solid;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                selection-background-color: #585b70;
            }
        """)

class ProviderButton(ModernButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton:checked {
                background-color: #cba6f7;
                color: #1e1e2e;
            }
            QPushButton:disabled {
                background-color: #313244;
                color: #6c7086;
            }
        """)

class ModelButton(ModernButton):
    def __init__(self, model_name, parent=None):
        super().__init__(model_name, parent)
        self.model_name = model_name
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:checked {
                background-color: #cba6f7;
                color: #1e1e2e;
            }
        """)

class APIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter API Keys")
        self.setModal(True)
        self.layout = QVBoxLayout(self)

        self.groq_key = QLineEdit(self)
        self.anthropic_key = QLineEdit(self)
        self.openai_key = QLineEdit(self)
        self.ollama_ip = QLineEdit(self)

        self.layout.addWidget(QLabel("Groq API Key:"))
        self.layout.addWidget(self.groq_key)
        self.layout.addWidget(QLabel("Anthropic API Key:"))
        self.layout.addWidget(self.anthropic_key)
        self.layout.addWidget(QLabel("OpenAI API Key:"))
        self.layout.addWidget(self.openai_key)
        self.layout.addWidget(QLabel("Ollama IP Address:"))
        self.layout.addWidget(self.ollama_ip)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #6c7086;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
        """)

    def get_keys(self):
        return {
            "groq": self.groq_key.text(),
            "anthropic": self.anthropic_key.text(),
            "openai": self.openai_key.text(),
            "ollama_ip": self.ollama_ip.text()
        }

class SettingsDialog(QDialog):
    def __init__(self, parent=None, api_keys=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.api_keys = api_keys or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.api_tab = QWidget()
        self.api_layout = QVBoxLayout(self.api_tab)

        self.groq_key = QLineEdit(self)
        self.groq_key.setText(self.api_keys.get('groq', ''))
        self.anthropic_key = QLineEdit(self)
        self.anthropic_key.setText(self.api_keys.get('anthropic', ''))
        self.openai_key = QLineEdit(self)
        self.openai_key.setText(self.api_keys.get('openai', ''))
        self.ollama_ip = QLineEdit(self)
        self.ollama_ip.setText(self.api_keys.get('ollama_ip', ''))

        self.api_layout.addWidget(QLabel("Groq API Key:"))
        self.api_layout.addWidget(self.groq_key)
        self.api_layout.addWidget(QLabel("Anthropic API Key:"))
        self.api_layout.addWidget(self.anthropic_key)
        self.api_layout.addWidget(QLabel("OpenAI API Key:"))
        self.api_layout.addWidget(self.openai_key)
        self.api_layout.addWidget(QLabel("Ollama IP Address:"))
        self.api_layout.addWidget(self.ollama_ip)

        self.tabs.addTab(self.api_tab, "API Keys")

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.setStyleSheet("""
            QDialog, QTabWidget, QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #6c7086;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QTabBar::tab {
                background-color: #313244;
                color: #cdd6f4;
                padding: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #45475a;
            }
        """)

    def get_keys(self):
        return {
            "groq": self.groq_key.text(),
            "anthropic": self.anthropic_key.text(),
            "openai": self.openai_key.text(),
            "ollama_ip": self.ollama_ip.text()
        }

class CollaborationSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Collaboration Settings")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.rounds_label = QLabel("Number of Interaction Rounds (0 for infinite):")
        self.rounds_input = QSpinBox()
        self.rounds_input.setRange(0, 10000)
        self.rounds_input.setValue(0)
        layout.addWidget(self.rounds_label)
        layout.addWidget(self.rounds_input)

        self.max_tokens_label = QLabel("Max Tokens per Response:")
        self.max_tokens_input = QLineEdit()
        self.max_tokens_input.setText("1000")
        layout.addWidget(self.max_tokens_label)
        layout.addWidget(self.max_tokens_input)

        self.temperature_label = QLabel("Temperature (0.0 - 1.0):")
        self.temperature_input = QLineEdit()
        self.temperature_input.setText("0.7")
        layout.addWidget(self.temperature_label)
        layout.addWidget(self.temperature_input)

        self.model1_role_label = QLabel("Role for Model 1:")
        self.model1_role_dropdown = ModernComboBox()
        self.model1_role_dropdown.addItems(Role.ROLES)
        layout.addWidget(self.model1_role_label)
        layout.addWidget(self.model1_role_dropdown)

        self.model2_role_label = QLabel("Role for Model 2:")
        self.model2_role_dropdown = ModernComboBox()
        self.model2_role_dropdown.addItems(Role.ROLES)
        layout.addWidget(self.model2_role_label)
        layout.addWidget(self.model2_role_dropdown)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit, QSpinBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #6c7086;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
        """)

    def get_settings(self):
        return {
            "rounds": int(self.rounds_input.value()),
            "max_tokens": int(self.max_tokens_input.text()),
            "temperature": float(self.temperature_input.text()),
            "model1_role": self.model1_role_dropdown.currentText(),
            "model2_role": self.model2_role_dropdown.currentText()
        }

class Role:
    ROLES = [
        "General Assistant",
        "Technical Expert",
        "Creative Thinker",
        "Data Analyst",
        "Healthcare Advisor",
        "Educational Tutor",
        "Scientific Researcher",
        "Project Manager",
        "Philosopher",
        "Debater",
        "Marketing Specialist",
        "Financial Advisor",
        "Legal Consultant",
        "Customer Support Agent",
        "Sports Analyst",
        "News Reporter",
        "Historian",
        "Psychologist",
        "Environmental Activist",
        "Chef"
    ]

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.formatter = HtmlFormatter(style='monokai')

    def highlightBlock(self, text):
        highlighted = highlight(text, PythonLexer(), self.formatter)
        soup = BeautifulSoup(highlighted, 'html.parser')

        format_dict = {
            'k': QColor('#f92672'),  # Keyword
            's': QColor('#e6db74'),  # String
            'c': QColor('#75715e'),  # Comment
            'n': QColor('#a6e22e'),  # Name
            'o': QColor('#f92672'),  # Operator
            'p': QColor('#f8f8f2'),  # Punctuation
        }

        self.setFormat(0, len(text), QTextCharFormat())  # Reset format

        pos = 0
        for tag in soup.find_all(['span']):
            class_name = tag.get('class', [None])[0]
            if class_name in format_dict:
                color = format_dict[class_name]
                char_format = QTextCharFormat()
                char_format.setForeground(color)
                start = text.find(tag.get_text(), pos)
                end = start + len(tag.get_text())
                self.setFormat(start, end - start, char_format)
                pos = end

class ChatBox(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.model_colors = {}

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Segoe UI", 11))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                padding: 10px;
                border-radius: 10px;
            }
        """)
        self.highlighter = CodeHighlighter(self.chat_display.document())
        layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        self.chat_input.setFont(QFont("Segoe UI", 11))
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #6c7086;
                padding: 10px;
                border-radius: 8px;
            }
        """)
        self.send_button = ModernButton("Send")
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        self.send_button.clicked.connect(self.send_message)
        self.chat_input.returnPressed.connect(self.send_message)

        self.current_model_name = ""
        self.current_is_user = False

    def send_message(self):
        message = self.chat_input.text().strip()
        if message:
            self.main_window.handle_message(message)
            self.chat_input.clear()

    def display_message(self, message, is_user=False, append=False):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        format = QTextCharFormat()
        format.setFont(QFont("Segoe UI", 11))
        if not append:
            cursor.insertText("\n")  # Ensure new messages start on a new line
            if is_user:
                format.setForeground(QColor("#89b4fa"))
                format.setFontWeight(QFont.Bold)
                cursor.insertText("You: ", format)
                format.setFontWeight(QFont.Normal)
                cursor.insertText(message, format)
            else:
                # Extract model name and content
                if ":" in message:
                    model_name, content = message.split(":", 1)
                    self.current_model_name = model_name.strip()
                    color = self.model_colors.get(self.current_model_name, QColor("#cdd6f4"))
                    format.setForeground(color)
                    format.setFontWeight(QFont.Bold)
                    cursor.insertText(f"{self.current_model_name}: ", format)
                    format.setFontWeight(QFont.Normal)
                    format.setForeground(QColor("#cdd6f4"))
                    cursor.insertText(content.strip(), format)
                else:
                    format.setForeground(QColor("#cdd6f4"))
                    cursor.insertText(message, format)
            cursor.insertText("\n")  # Ensure separation between messages
        else:
            # Append to the last message
            format.setForeground(QColor("#cdd6f4"))
            cursor.insertText(message, format)

        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def clear_chat(self):
        self.chat_display.clear()

class VisualizationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setTheme(QChart.ChartThemeDark)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        layout.addWidget(self.chart_view)

    def update_chart(self, data):
        QMetaObject.invokeMethod(self, "update_chart_internal", Qt.QueuedConnection, Q_ARG(dict, data))

    @pyqtSlot(dict)
    def update_chart_internal(self, data):
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        bar_series = QBarSeries()
        line_series_list = []

        axis_x = QValueAxis()
        axis_x.setTitleText("Round")
        self.chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = QValueAxis()
        axis_y.setTitleText("Response Time (s)")
        self.chart.addAxis(axis_y, Qt.AlignLeft)

        max_rounds = 0

        for model, times in data.items():
            bar_set = QBarSet(model)
            bar_set.append(times)
            bar_series.append(bar_set)

            line_series = QLineSeries()
            line_series.setName(model)
            for i, time in enumerate(times):
                line_series.append(i + 1, time)
            line_series_list.append(line_series)

            max_rounds = max(max_rounds, len(times))

        axis_x.setRange(1, max_rounds)
        axis_x.setTickCount(max_rounds)

        self.chart.addSeries(bar_series)
        bar_series.attachAxis(axis_x)
        bar_series.attachAxis(axis_y)

        for line_series in line_series_list:
            self.chart.addSeries(line_series)
            line_series.attachAxis(axis_x)
            line_series.attachAxis(axis_y)

        self.chart.setTitle("Model Response Times")
        self.chart_view.setChart(self.chart)

class ControlPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        self.mode_tabs = QTabWidget()
        self.mode_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #6c7086;
                background: #1e1e2e;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #313244;
                color: #cdd6f4;
                padding: 10px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #45475a;
            }
        """)
        layout.addWidget(self.mode_tabs)

        self.init_single_model_tab()
        self.init_collab_tab()

        self.visualization = VisualizationWidget()
        layout.addWidget(self.visualization)

        self.init_control_buttons(layout)
        self.init_status_bar(layout)

        self.mode_tabs.currentChanged.connect(self.toggle_mode)
        self.start_collab_button.clicked.connect(self.main_window.start_collaboration)
        self.stop_button.clicked.connect(self.main_window.stop_chat)
        self.clear_chat_button.clicked.connect(self.main_window.clear_chat)
        self.collab_settings_button.clicked.connect(self.main_window.show_collaboration_settings)

    def init_single_model_tab(self):
        single_model_widget = QWidget()
        single_model_layout = QVBoxLayout(single_model_widget)

        self.provider_buttons_layout = QHBoxLayout()
        self.openai_button = ProviderButton("OpenAI")
        self.anthropic_button = ProviderButton("Anthropic")
        self.groq_button = ProviderButton("Groq")
        self.ollama_button = ProviderButton("Ollama")

        self.openai_button.clicked.connect(lambda: self.select_provider("OpenAI"))
        self.anthropic_button.clicked.connect(lambda: self.select_provider("Anthropic"))
        self.groq_button.clicked.connect(lambda: self.select_provider("Groq"))
        self.ollama_button.clicked.connect(lambda: self.select_provider("Ollama"))

        self.provider_buttons_layout.addWidget(self.openai_button)
        self.provider_buttons_layout.addWidget(self.anthropic_button)
        self.provider_buttons_layout.addWidget(self.groq_button)
        self.provider_buttons_layout.addWidget(self.ollama_button)

        single_model_layout.addLayout(self.provider_buttons_layout)

        self.model_buttons_scroll_area = QScrollArea()
        self.model_buttons_widget = QWidget()
        self.model_buttons_layout = QGridLayout(self.model_buttons_widget)
        self.model_buttons_scroll_area.setWidget(self.model_buttons_widget)
        self.model_buttons_scroll_area.setWidgetResizable(True)
        self.model_buttons_scroll_area.setFixedHeight(200)
        self.model_buttons_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #6c7086;
                border-radius: 8px;
                background-color: #1e1e2e;
            }
            QScrollBar:vertical {
                background: #313244;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #45475a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        single_model_layout.addWidget(self.model_buttons_scroll_area)

        single_model_layout.addWidget(QLabel("Role for the model:"))
        self.role_dropdown = ModernComboBox()
        self.role_dropdown.addItems(Role.ROLES)
        single_model_layout.addWidget(self.role_dropdown)

        self.chain_of_thought_checkbox = QCheckBox("Enable Chain of Thought")
        self.chain_of_thought_checkbox.setStyleSheet("""
            QCheckBox {
                color: #cdd6f4;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #6c7086;
            }
            QCheckBox::indicator:unchecked {
                background-color: #313244;
            }
            QCheckBox::indicator:checked {
                background-color: #cba6f7;
            }
        """)
        single_model_layout.addWidget(self.chain_of_thought_checkbox)

        self.mode_tabs.addTab(single_model_widget, "Single Model")

    def init_collab_tab(self):
        collab_widget = QWidget()
        collab_layout = QVBoxLayout(collab_widget)

        collab_layout.addWidget(QLabel("Model 1 Provider:"))
        self.provider_buttons_layout1 = QHBoxLayout()
        self.model1_openai_button = ProviderButton("OpenAI")
        self.model1_anthropic_button = ProviderButton("Anthropic")
        self.model1_groq_button = ProviderButton("Groq")
        self.model1_ollama_button = ProviderButton("Ollama")

        self.model1_openai_button.clicked.connect(lambda: self.select_provider1("OpenAI"))
        self.model1_anthropic_button.clicked.connect(lambda: self.select_provider1("Anthropic"))
        self.model1_groq_button.clicked.connect(lambda: self.select_provider1("Groq"))
        self.model1_ollama_button.clicked.connect(lambda: self.select_provider1("Ollama"))

        self.provider_buttons_layout1.addWidget(self.model1_openai_button)
        self.provider_buttons_layout1.addWidget(self.model1_anthropic_button)
        self.provider_buttons_layout1.addWidget(self.model1_groq_button)
        self.provider_buttons_layout1.addWidget(self.model1_ollama_button)
        collab_layout.addLayout(self.provider_buttons_layout1)

        self.model1_buttons_scroll_area = QScrollArea()
        self.model1_buttons_widget = QWidget()
        self.model1_buttons_layout = QGridLayout(self.model1_buttons_widget)
        self.model1_buttons_scroll_area.setWidget(self.model1_buttons_widget)
        self.model1_buttons_scroll_area.setWidgetResizable(True)
        self.model1_buttons_scroll_area.setFixedHeight(150)
        self.model1_buttons_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #6c7086;
                border-radius: 8px;
                background-color: #1e1e2e;
            }
            QScrollBar:vertical {
                background: #313244;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #45475a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        collab_layout.addWidget(self.model1_buttons_scroll_area)

        collab_layout.addWidget(QLabel("Model 1 Role:"))
        self.model1_role_dropdown = ModernComboBox()
        self.model1_role_dropdown.addItems(Role.ROLES)
        collab_layout.addWidget(self.model1_role_dropdown)

        collab_layout.addWidget(QLabel("Model 2 Provider:"))
        self.provider_buttons_layout2 = QHBoxLayout()
        self.model2_openai_button = ProviderButton("OpenAI")
        self.model2_anthropic_button = ProviderButton("Anthropic")
        self.model2_groq_button = ProviderButton("Groq")
        self.model2_ollama_button = ProviderButton("Ollama")

        self.model2_openai_button.clicked.connect(lambda: self.select_provider2("OpenAI"))
        self.model2_anthropic_button.clicked.connect(lambda: self.select_provider2("Anthropic"))
        self.model2_groq_button.clicked.connect(lambda: self.select_provider2("Groq"))
        self.model2_ollama_button.clicked.connect(lambda: self.select_provider2("Ollama"))

        self.provider_buttons_layout2.addWidget(self.model2_openai_button)
        self.provider_buttons_layout2.addWidget(self.model2_anthropic_button)
        self.provider_buttons_layout2.addWidget(self.model2_groq_button)
        self.provider_buttons_layout2.addWidget(self.model2_ollama_button)
        collab_layout.addLayout(self.provider_buttons_layout2)

        self.model2_buttons_scroll_area = QScrollArea()
        self.model2_buttons_widget = QWidget()
        self.model2_buttons_layout = QGridLayout(self.model2_buttons_widget)
        self.model2_buttons_scroll_area.setWidget(self.model2_buttons_widget)
        self.model2_buttons_scroll_area.setWidgetResizable(True)
        self.model2_buttons_scroll_area.setFixedHeight(150)
        self.model2_buttons_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #6c7086;
                border-radius: 8px;
                background-color: #1e1e2e;
            }
            QScrollBar:vertical {
                background: #313244;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #45475a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        collab_layout.addWidget(self.model2_buttons_scroll_area)

        collab_layout.addWidget(QLabel("Model 2 Role:"))
        self.model2_role_dropdown = ModernComboBox()
        self.model2_role_dropdown.addItems(Role.ROLES)
        collab_layout.addWidget(self.model2_role_dropdown)

        self.start_collab_button = ModernButton("Start Collaboration")
        collab_layout.addWidget(self.start_collab_button)
        self.collab_settings_button = ModernButton("Collaboration Settings")
        collab_layout.addWidget(self.collab_settings_button)

        self.mode_tabs.addTab(collab_widget, "Collaboration")

    def init_control_buttons(self, layout):
        control_buttons_layout = QHBoxLayout()
        self.stop_button = ModernButton("Stop")
        self.clear_chat_button = ModernButton("Clear Chat")
        control_buttons_layout.addWidget(self.stop_button)
        control_buttons_layout.addWidget(self.clear_chat_button)
        layout.addLayout(control_buttons_layout)

    def init_status_bar(self, layout):
        self.status_bar = QProgressBar()
        self.status_bar.setTextVisible(False)
        self.status_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #6c7086;
                border-radius: 5px;
                text-align: center;
                background-color: #313244;
            }
            QProgressBar::chunk {
                background-color: #cba6f7;
                width: 20px;
            }
        """)
        layout.addWidget(self.status_bar)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setStyleSheet("color: #cdd6f4; font-weight: bold;")
        layout.addWidget(self.status_label)

    def toggle_mode(self, index):
        self.main_window.current_mode = "collaboration" if index == 1 else "single"

    def update_status(self, status, progress=0):
        QMetaObject.invokeMethod(self, "update_status_internal", Qt.QueuedConnection, Q_ARG(str, status), Q_ARG(int, progress))

    @pyqtSlot(str, int)
    def update_status_internal(self, status, progress):
        self.status_label.setText(f"Status: {status}")
        self.status_bar.setValue(progress)
        self.main_window.statusBar().showMessage(status)

    def start_progress_animation(self):
        QMetaObject.invokeMethod(self, "start_progress_animation_internal", Qt.QueuedConnection)

    @pyqtSlot()
    def start_progress_animation_internal(self):
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress_animation)
        self.progress_timer.start(50)

    def update_progress_animation(self):
        current_value = self.status_bar.value()
        self.status_bar.setValue((current_value + 1) % 101)

    def stop_progress_animation(self):
        QMetaObject.invokeMethod(self, "stop_progress_animation_internal", Qt.QueuedConnection)

    @pyqtSlot()
    def stop_progress_animation_internal(self):
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        self.status_bar.setValue(0)

    def select_provider(self, provider_name):
        self.main_window.selected_provider = provider_name
        self.update_models_buttons(provider_name)
        self.highlight_selected_provider(provider_name)

    def highlight_selected_provider(self, provider_name):
        for button in [self.openai_button, self.anthropic_button, self.groq_button, self.ollama_button]:
            if button.text() == provider_name:
                button.setChecked(True)
            else:
                button.setChecked(False)

    def update_models_buttons(self, provider_name):
        for i in reversed(range(self.model_buttons_layout.count())):
            widget_to_remove = self.model_buttons_layout.itemAt(i).widget()
            self.model_buttons_layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        models = self.main_window.models.get(provider_name, [])
        columns = 2
        for index, model in enumerate(models):
            row = index // columns
            col = index % columns
            model_button = ModelButton(model)
            model_button.clicked.connect(lambda checked, m=model: self.select_model(m))
            self.model_buttons_layout.addWidget(model_button, row, col)

    def select_model(self, model_name):
        self.main_window.selected_model = model_name
        self.highlight_selected_model(model_name)

    def highlight_selected_model(self, model_name):
        for i in range(self.model_buttons_layout.count()):
            button = self.model_buttons_layout.itemAt(i).widget()
            if button.model_name == model_name:
                button.setChecked(True)
            else:
                button.setChecked(False)

    def select_provider1(self, provider_name):
        self.main_window.selected_provider1 = provider_name
        self.update_models_buttons1(provider_name)
        self.highlight_selected_provider1(provider_name)

    def highlight_selected_provider1(self, provider_name):
        for button in [self.model1_openai_button, self.model1_anthropic_button, self.model1_groq_button, self.model1_ollama_button]:
            if button.text() == provider_name:
                button.setChecked(True)
            else:
                button.setChecked(False)

    def update_models_buttons1(self, provider_name):
        for i in reversed(range(self.model1_buttons_layout.count())):
            widget_to_remove = self.model1_buttons_layout.itemAt(i).widget()
            self.model1_buttons_layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        models = self.main_window.models.get(provider_name, [])
        columns = 2
        for index, model in enumerate(models):
            row = index // columns
            col = index % columns
            model_button = ModelButton(model)
            model_button.clicked.connect(lambda checked, m=model: self.select_model1(m))
            self.model1_buttons_layout.addWidget(model_button, row, col)

    def select_model1(self, model_name):
        self.main_window.selected_model1 = model_name
        self.highlight_selected_model1(model_name)

    def highlight_selected_model1(self, model_name):
        for i in range(self.model1_buttons_layout.count()):
            button = self.model1_buttons_layout.itemAt(i).widget()
            if button.model_name == model_name:
                button.setChecked(True)
            else:
                button.setChecked(False)

    def select_provider2(self, provider_name):
        self.main_window.selected_provider2 = provider_name
        self.update_models_buttons2(provider_name)
        self.highlight_selected_provider2(provider_name)

    def highlight_selected_provider2(self, provider_name):
        for button in [self.model2_openai_button, self.model2_anthropic_button, self.model2_groq_button, self.model2_ollama_button]:
            if button.text() == provider_name:
                button.setChecked(True)
            else:
                button.setChecked(False)

    def update_models_buttons2(self, provider_name):
        for i in reversed(range(self.model2_buttons_layout.count())):
            widget_to_remove = self.model2_buttons_layout.itemAt(i).widget()
            self.model2_buttons_layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        models = self.main_window.models.get(provider_name, [])
        columns = 2
        for index, model in enumerate(models):
            row = index // columns
            col = index % columns
            model_button = ModelButton(model)
            model_button.clicked.connect(lambda checked, m=model: self.select_model2(m))
            self.model2_buttons_layout.addWidget(model_button, row, col)

    def select_model2(self, model_name):
        self.main_window.selected_model2 = model_name
        self.highlight_selected_model2(model_name)

    def highlight_selected_model2(self, model_name):
        for i in range(self.model2_buttons_layout.count()):
            button = self.model2_buttons_layout.itemAt(i).widget()
            if button.model_name == model_name:
                button.setChecked(True)
            else:
                button.setChecked(False)

class WorkerThread(QThread):
    response_received = pyqtSignal(str, bool)
    response_finished = pyqtSignal(float)

    def __init__(self, main_window, model, prompt, max_tokens, temperature):
        super().__init__()
        self.main_window = main_window
        self.model = model
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.temperature = temperature

    def run(self):
        start_time = time.time()
        try:
            if self.model.startswith("Groq: "):
                self.get_groq_response()
            elif self.model.startswith("Ollama: "):
                self.get_ollama_response()
            elif self.model.startswith("Anthropic: "):
                self.get_anthropic_response()
            elif self.model.startswith("OpenAI: "):
                self.get_openai_response()
            else:
                self.response_received.emit("Invalid model selected.", False)
        except Exception as e:
            self.response_received.emit(f"Error: {str(e)}", False)
        finally:
            end_time = time.time()
            self.response_finished.emit(end_time - start_time)

    def get_groq_response(self):
        headers = self.main_window.HEADERS['groq']
        response = requests.post(
            self.main_window.API_URLS['groq_llm'],
            headers=headers,
            json={
                "model": self.model.replace("Groq: ", ""),
                "messages": [{"role": "user", "content": self.prompt}],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": True
            },
            stream=True
        )
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                try:
                    data_line = line.decode('utf-8')
                    if data_line.startswith("data: "):
                        chunk = json.loads(data_line[6:])
                        if 'choices' in chunk:
                            delta = chunk['choices'][0]['delta']
                            if 'content' in delta:
                                token = delta['content']
                                self.response_received.emit(token, True)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON: {line}")
                except Exception as e:
                    print(f"Error processing chunk: {e}")

    def get_ollama_response(self):
        response = requests.post(
            self.main_window.API_URLS['ollama_llm'],
            json={
                'model': self.model.replace("Ollama: ", ""),
                'prompt': self.prompt,
                'options': {
                    'num_predict': self.max_tokens,
                    'temperature': self.temperature
                }
            },
            stream=True
        )
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line)
                    if 'done' in json_line and json_line['done']:
                        break
                    if 'response' in json_line:
                        self.response_received.emit(json_line['response'], True)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON: {line}")

    def get_anthropic_response(self):
        if self.main_window.anthropic_client:
            try:
                with self.main_window.anthropic_client.messages.stream(
                    model=self.model.replace("Anthropic: ", ""),
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[
                        {"role": "user", "content": self.prompt}
                    ]
                ) as stream:
                    for text in stream.text_stream:
                        self.response_received.emit(text, True)
            except Exception as e:
                self.response_received.emit(f"Error: {str(e)}", False)
        else:
            self.response_received.emit("Anthropic API key not provided.", False)

    def get_openai_response(self):
        if self.main_window.openai_client:
            try:
                stream = self.main_window.openai_client.chat.completions.create(
                    model=self.model.replace("OpenAI: ", ""),
                    messages=[{"role": "user", "content": self.prompt}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        self.response_received.emit(chunk.choices[0].delta.content, True)
            except Exception as e:
                self.response_received.emit(f"Error: {str(e)}", False)
        else:
            self.response_received.emit("OpenAI API key not provided.", False)

class MainWindow(QMainWindow):
    update_chat_signal = pyqtSignal(str, bool, bool)
    update_status_signal = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced LLM Collaboration App")
        self.setGeometry(100, 100, 1200, 800)

        self.api_keys = self.get_api_keys()
        self.init_clients()

        self.API_URLS = {
            "groq_models": "https://api.groq.com/openai/v1/models",
            "groq_llm": "https://api.groq.com/openai/v1/chat/completions",
            "ollama_models": f"http://{self.api_keys.get('ollama_ip', '')}:11434/api/tags",
            "ollama_llm": f"http://{self.api_keys.get('ollama_ip', '')}:11434/api/generate",
            "openai_llm": "https://api.openai.com/v1/chat/completions",
            "anthropic_llm": "https://api.anthropic.com/v1/messages"
        }

        self.HEADERS = {
            "groq": {
                "Authorization": f"Bearer {self.api_keys.get('groq', '')}",
                "Content-Type": "application/json"
            },
            "anthropic": {
                "x-api-key": f"{self.api_keys.get('anthropic', '')}",
                "content-type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        }

        self.current_theme = Theme.DARK

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.chat_box = ChatBox(self)
        self.control_panel = ControlPanel(self)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.chat_box)
        splitter.addWidget(self.control_panel)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

        self.current_mode = "single"
        self.stop_event = threading.Event()
        self.collaboration_models = []
        self.conversation_history = []
        self.current_response = ""
        self.model_colors = {}
        self.response_times = defaultdict(list)

        self.collab_settings = {
            "rounds": 0,  # 0 indicates infinite rounds
            "max_tokens": 1000,
            "temperature": 0.7,
            "model1_role": "General Assistant",
            "model2_role": "Technical Expert"
        }

        self.role_prompts = {
            "General Assistant": "You are a helpful assistant. 😊",
            "Technical Expert": "You are an expert in technology. 🛠️",
            "Creative Thinker": "You are a creative thinker. ✍️",
            "Data Analyst": "You are a data analyst. 📊",
            "Healthcare Advisor": "You are a healthcare advisor. 🏥",
            "Educational Tutor": "You are an educational tutor. 📚",
            "Scientific Researcher": "You are a scientific researcher. 🧪",
            "Project Manager": "You are a project manager. 📋",
            "Philosopher": "You are a philosopher. 🤔",
            "Debater": "You are a skilled debater. 💬",
            "Marketing Specialist": "You are a marketing specialist. 📈",
            "Financial Advisor": "You are a financial advisor. 💰",
            "Legal Consultant": "You are a legal consultant. ⚖️",
            "Customer Support Agent": "You are a customer support agent. ☎️",
            "Sports Analyst": "You are a sports analyst. 🏅",
            "News Reporter": "You are a news reporter. 📰",
            "Historian": "You are a historian. 🏛️",
            "Psychologist": "You are a psychologist. 🧠",
            "Environmental Activist": "You are an environmental activist. 🌍",
            "Chef": "You are a chef. 🍳"
        }

        self.create_toolbar()
        self.apply_theme(self.current_theme)
        self.models = {}
        self.fetch_all_models()

        self.statusBar().showMessage("Ready")

        self.update_chat_signal.connect(self.chat_box.display_message)
        self.update_status_signal.connect(self.control_panel.update_status)

        self.worker_thread = None
        self.collab_round = 1  # Initialize collaboration round
        self.current_collab_model_index = 0  # For managing model sequence

        self.selected_provider = None
        self.selected_provider1 = None
        self.selected_provider2 = None

        self.selected_model = None
        self.selected_model1 = None
        self.selected_model2 = None

    def get_api_keys(self):
        dialog = APIKeyDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_keys()
        else:
            return {}

    def init_clients(self):
        if self.api_keys.get('anthropic'):
            self.anthropic_client = anthropic.Anthropic(api_key=self.api_keys['anthropic'])
        else:
            self.anthropic_client = None

        if self.api_keys.get('openai'):
            self.openai_client = openai.OpenAI(api_key=self.api_keys['openai'])
        else:
            self.openai_client = None

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #1e1e2e;
                border: none;
                spacing: 10px;
            }
            QToolButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }
            QToolButton:hover {
                background-color: #585b70;
            }
        """)

        start_action = QAction("Start", self)
        start_action.triggered.connect(self.start_collaboration)
        toolbar.addAction(start_action)

        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.stop_chat)
        toolbar.addAction(stop_action)

        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self.clear_chat)
        toolbar.addAction(clear_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(settings_action)

        self.addToolBar(toolbar)

    def apply_theme(self, theme):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {theme['bg']};
                color: {theme['text']};
            }}
            QPushButton {{
                background-color: {theme['button']};
                color: {theme['text']};
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {theme['input']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 5px;
                border-radius: 5px;
            }}
            QScrollBar:vertical {{
                background: {theme['scroll_bg']};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['scroll_handle']};
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def fetch_all_models(self):
        self.control_panel.start_progress_animation()
        self.update_status_signal.emit("Fetching models...", 0)

        try:
            if self.api_keys.get('groq'):
                groq_models = self.fetch_groq_models()
                self.models['Groq'] = groq_models
            else:
                self.control_panel.groq_button.setEnabled(False)
                self.control_panel.model1_groq_button.setEnabled(False)
                self.control_panel.model2_groq_button.setEnabled(False)

            if self.api_keys.get('ollama_ip'):
                ollama_models = self.fetch_ollama_models()
                self.models['Ollama'] = ollama_models
            else:
                self.control_panel.ollama_button.setEnabled(False)
                self.control_panel.model1_ollama_button.setEnabled(False)
                self.control_panel.model2_ollama_button.setEnabled(False)

            if self.api_keys.get('anthropic'):
                anthropic_models = self.fetch_anthropic_models()
                self.models['Anthropic'] = anthropic_models
            else:
                self.control_panel.anthropic_button.setEnabled(False)
                self.control_panel.model1_anthropic_button.setEnabled(False)
                self.control_panel.model2_anthropic_button.setEnabled(False)

            if self.api_keys.get('openai'):
                openai_models = self.fetch_openai_models()
                self.models['OpenAI'] = openai_models
            else:
                self.control_panel.openai_button.setEnabled(False)
                self.control_panel.model1_openai_button.setEnabled(False)
                self.control_panel.model2_openai_button.setEnabled(False)

        except Exception as e:
            self.show_error_message(f"Error fetching models: {str(e)}")
        finally:
            self.control_panel.stop_progress_animation()
            self.update_status_signal.emit("Models fetched", 100)
            QTimer.singleShot(2000, lambda: self.update_status_signal.emit("Idle", 0))

    def fetch_groq_models(self):
        headers = self.HEADERS['groq']
        response = requests.get(self.API_URLS['groq_models'], headers=headers)
        response.raise_for_status()
        models_data = response.json()
        return [f"{model.get('id', 'Unknown')}" for model in models_data.get("data", [])]

    def fetch_ollama_models(self):
        response = requests.get(self.API_URLS['ollama_models'])
        response.raise_for_status()
        data = response.json()
        return [f"{model['name']}" for model in data.get('models', [])]

    def fetch_anthropic_models(self):
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-3-5-sonnet-20240620"
        ]

    def fetch_openai_models(self):
        if self.openai_client:
            try:
                models = self.openai_client.models.list()
                return [f"{model.id}" for model in models.data if "gpt" in model.id.lower()]
            except Exception as e:
                self.show_error_message(f"Error fetching OpenAI models: {str(e)}")
                return []
        else:
            return []

    @pyqtSlot()
    def handle_message(self, message):
        self.chat_box.display_message(message, is_user=True)
        self.control_panel.start_progress_animation()
        self.update_status_signal.emit("Processing", 0)
        self.stop_event.clear()

        if self.current_mode == "collaboration" and self.collaboration_models:
            self.conversation_history.append({"role": "user", "content": message})
            self.collaborative_interaction(message)
        else:
            selected_model = self.selected_model
            if selected_model:
                selected_role = self.control_panel.role_dropdown.currentText()
                chain_of_thought = self.control_panel.chain_of_thought_checkbox.isChecked()
                self.single_model_response(selected_model, selected_role, message, chain_of_thought)
            else:
                self.show_error_message("Please select a provider and model.")

    def single_model_response(self, model, role, user_message, chain_of_thought):
        role_prompt = self.role_prompts.get(role, "You are a general assistant. 😊")

        full_prompt = f"{role_prompt}\n{user_message}"

        if chain_of_thought:
            full_prompt += "\n\nPlease use the following structure for your response:\n"
            full_prompt += "<thinking>\n- Break down the problem\n- Outline your approach\n- Consider alternatives\n</thinking>\n\n"
            full_prompt += "<reflection>\n- Review your reasoning\n- Identify potential issues\n- Suggest improvements\n</reflection>\n\n"
            full_prompt += "<output>\nYour final response here.\n</output>"

        self.current_response = ""  # Reset current_response
        display_model_name = model  # Since model names are now without provider prefixes
        self.model_colors = {display_model_name: QColor("#cba6f7")}  # Assign default color
        self.chat_box.model_colors = self.model_colors

        full_model_name = f"{self.selected_provider}: {model}"

        self.worker_thread = WorkerThread(
            self, full_model_name, full_prompt,
            self.collab_settings["max_tokens"],
            self.collab_settings["temperature"]
        )
        self.worker_thread.response_received.connect(lambda text, append: self.handle_model_response(text, append, display_model_name))
        self.worker_thread.response_finished.connect(self.handle_response_finished)
        self.worker_thread.start()

    def collaborative_interaction(self, user_message):
        self.current_collab_model_index = 0
        self.collab_round = 1
        self.process_next_collab_model()

    def process_next_collab_model(self):
        if self.current_collab_model_index < len(self.collaboration_models):
            model = self.collaboration_models[self.current_collab_model_index]
            role_dropdown = self.control_panel.model1_role_dropdown if self.current_collab_model_index == 0 else self.control_panel.model2_role_dropdown
            role = role_dropdown.currentText()
            role_prompt = self.role_prompts.get(role, "")
            prompt = f"{role_prompt}\n{self.format_conversation_history()}"
            self.current_response = ""  # Reset current_response

            display_model_name = model.split(": ")[1]
            self.worker_thread = WorkerThread(
                self, model, prompt,
                self.collab_settings["max_tokens"],
                self.collab_settings["temperature"]
            )
            self.worker_thread.response_received.connect(lambda text, append: self.handle_model_response(text, append, display_model_name))
            self.worker_thread.response_finished.connect(lambda time: self.handle_response_finished(time, display_model_name))
            self.worker_thread.start()
        else:
            # Collaboration round finished
            self.control_panel.stop_progress_animation()
            self.update_status_signal.emit("Collaboration round finished", 100)
            QTimer.singleShot(2000, lambda: self.update_status_signal.emit("Idle", 0))
            # Reset for next round if applicable
            if self.collab_settings["rounds"] == 0 or self.collab_round < self.collab_settings["rounds"]:
                self.collab_round += 1
                self.current_collab_model_index = 0
                self.process_next_collab_model()

    def handle_model_response(self, text, append, model=""):
        if not append:
            self.current_response = ""
            self.current_response += text
            # Start new message with model name
            self.update_chat_signal.emit(f"{model}: {text}", False, False)
        else:
            self.current_response += text
            # Append text without model name
            self.update_chat_signal.emit(text, False, True)

    def handle_response_finished(self, response_time, model=""):
        if model:
            # Record the response time
            self.response_times[model].append(response_time)
            self.control_panel.visualization.update_chart(self.response_times)

            self.conversation_history.append({"role": "assistant", "content": f"{model}: {self.current_response}"})
            self.current_response = ""
            # Proceed to next model
            self.current_collab_model_index += 1
            self.process_next_collab_model()
        else:
            # Single model response finished
            self.control_panel.stop_progress_animation()
            self.update_status_signal.emit("Response received", 100)
            QTimer.singleShot(2000, lambda: self.update_status_signal.emit("Idle", 0))

    def format_conversation_history(self):
        formatted_history = ""
        for message in self.conversation_history:
            if message['role'] == 'system':
                formatted_history += f"System: {message['content']}\n\n"
            elif message['role'] == 'user':
                formatted_history += f"Human: {message['content']}\n\n"
            elif message['role'] == 'assistant':
                formatted_history += f"AI: {message['content']}\n\n"
        return formatted_history

    @pyqtSlot()
    def start_collaboration(self):
        model1_provider = self.selected_provider1
        model2_provider = self.selected_provider2
        model1_name = self.selected_model1
        model2_name = self.selected_model2
        if model1_provider and model1_name and model2_provider and model2_name:
            model1_full = f"{model1_provider}: {model1_name}"
            model2_full = f"{model2_provider}: {model2_name}"
            self.collaboration_models = [model1_full, model2_full]
            self.conversation_history = []
            # Assign colors to models
            self.model_colors = {
                model1_name: QColor("#cba6f7"),  # Purple
                model2_name: QColor("#89b4fa"),  # Blue
            }
            self.chat_box.model_colors = self.model_colors

            system_prompt = "You are participating in a collaborative discussion. Please engage with the other model and the user in a constructive manner."

            self.update_chat_signal.emit(f"Starting collaboration between models with prompt: {system_prompt}", False, False)
            self.update_status_signal.emit("Collaboration started", 0)
            self.conversation_history.append({"role": "system", "content": system_prompt})
        else:
            self.show_error_message("Please select providers and models for both Model 1 and Model 2.")

    @pyqtSlot()
    def stop_chat(self):
        self.stop_event.set()
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
        self.control_panel.stop_progress_animation()
        self.update_status_signal.emit("Chat stopped", 0)
        self.update_chat_signal.emit("Chat stopped by user.", False, False)
        QTimer.singleShot(2000, lambda: self.update_status_signal.emit("Idle", 0))

    @pyqtSlot()
    def clear_chat(self):
        self.chat_box.clear_chat()
        self.conversation_history = []
        self.update_status_signal.emit("Chat cleared", 0)
        QTimer.singleShot(2000, lambda: self.update_status_signal.emit("Idle", 0))

    def show_collaboration_settings(self):
        dialog = CollaborationSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.collab_settings = dialog.get_settings()
            self.statusBar().showMessage("Collaboration settings updated", 3000)

    def show_settings_dialog(self):
        dialog = SettingsDialog(self, api_keys=self.api_keys)
        if dialog.exec_() == QDialog.Accepted:
            self.api_keys = dialog.get_keys()
            self.init_clients()
            self.fetch_all_models()
            self.statusBar().showMessage("Settings updated", 3000)

    def show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QMessageBox QLabel {
                color: #cdd6f4;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
        """)
        msg_box.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())