import sys

from PyQt5.QtCore import QRegExp
from PyQt5.QtWidgets import QApplication, QWidget, QFormLayout, QLabel, QLineEdit, QPushButton, QMainWindow, \
    QStackedLayout, QComboBox, QCheckBox
from PyQt5.QtGui import QDoubleValidator, QColor, QRegExpValidator
from clicker_util import AutoClickerThread, Config, from_file
from numpy import format_float_positional as float_to_str

DEFAULTS_PATH = "../../Desktop/autoclicker/defaults.json"


class SubmittedWindow(QMainWindow):
    def __init__(self, parent):
        super(SubmittedWindow, self).__init__()
        self.setWindowTitle("AutoClicker - Idle")
        self.clicker_label = QLabel()
        self.form_layout = QFormLayout()
        self.container = QWidget()
        self.parent = parent
        self.exit_button = QPushButton("Exit")
        self.quit_button = QPushButton("Quit")
        self.run_info = Config()
        self.clicker_thread = AutoClickerThread(parent_ui=self)
        self.normal_palette = self.palette()
        self.clicking_palette = self.palette()
        self.clicking_palette.setColor(self.backgroundRole(), QColor(255, 200, 196))

    def closeEvent(self, event):
        self.exit_app()

    def run(self):
        self.exit_button.clicked.connect(self.exit_app)
        self.quit_button.clicked.connect(self.quit_app)
        if not self.run_info.input_mode:
            show_string = "<alt>" if self.run_info.alt_modifier else ""
            if self.run_info.key_combination:
                if self.run_info.alt_modifier:
                    show_string += "+"
                show_string += "+".join(self.run_info.key_combination)
        else:
            show_string = {0: "mouse button 4",
                           1: "mouse button 5"}.get(self.run_info.special_mouse_press)
        if self.run_info.output_type:
            output_string = ', '.join(self.run_info.output_sequence)
        else:
            output_string = {0: "left mouse button", 1: "right mouse button"}.get(self.run_info.mouse_output)
        self.clicker_label.setText(f"Watching for input: {show_string}" +
                                   f"{', with toggle' if self.run_info.toggle else ''}\n" +
                                   f"Outputting: {output_string}")
        self.form_layout.addRow(self.clicker_label)
        self.form_layout.addRow(self.exit_button)
        self.form_layout.addRow(self.quit_button)
        self.clicker_thread.set_config(self.run_info)
        self.container.setLayout(self.form_layout)
        self.setCentralWidget(self.container)
        self.clicker_thread.start()
        self.show()

    def exit_app(self):
        self.clicker_thread.stop()
        self.hide()
        self.parent.show()

    def quit_app(self):
        self.clicker_thread.stop()
        sys.exit(0)

    def update_clicking(self, is_clicking):
        if is_clicking:
            self.setWindowTitle("AutoClicker - Clicking")
            self.setPalette(self.clicking_palette)
        else:
            self.setWindowTitle("AutoClicker - Idle")
            self.setPalette(self.normal_palette)


class KeyboardWidgetView(QWidget):
    def __init__(self):
        super(KeyboardWidgetView, self).__init__()
        self.form_layout = QFormLayout()
        self.alt_modifier = QCheckBox()
        self.input_string = QLineEdit()
        self.form_layout.addRow(QLabel("Require left alt-key modifier: "), self.alt_modifier)
        self.form_layout.addRow(QLabel("Start on key combination: "), self.input_string)
        self.setLayout(self.form_layout)


class MouseWidgetView(QWidget):
    def __init__(self):
        super(MouseWidgetView, self).__init__()
        self.form_layout = QFormLayout()
        self.input_select = QComboBox()
        self.input_select.addItems(["Mouse button 4", "Mouse button 5"])
        self.form_layout.addRow(QLabel("Button for auto-clicking: "), self.input_select)
        self.setLayout(self.form_layout)


class KeyboardOutputWidgetView(QWidget):
    def __init__(self):
        super(KeyboardOutputWidgetView, self).__init__()
        self.form_layout = QFormLayout()
        self.input_sequence = QLineEdit()
        self.form_layout.addRow(QLabel("Output sequence: "), self.input_sequence)
        self.hold_time = QLineEdit()
        self.form_layout.addRow(QLabel("Key hold time: "), self.hold_time)
        self.setLayout(self.form_layout)

class MouseOutputWidgetView(QWidget):
    def __init__(self):
        super(MouseOutputWidgetView, self).__init__()
        self.form_layout = QFormLayout()
        self.output_selector = QComboBox()
        self.output_selector.addItems(["Mouse left button", "Mouse right button"])
        self.form_layout.addRow(QLabel("Mouse output: "), self.output_selector)
        self.setLayout(self.form_layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        self.setWindowTitle("AutoClicker")
        self.defaults = from_file(DEFAULTS_PATH)
        self.submit_view = None
        self.container = QWidget()
        self.form_layout = QFormLayout()
        self.input_subview_container = QWidget()
        self.output_subview_container = QWidget()
        self.input_subview_switch_combo = QComboBox()
        self.output_subview_switch_combo = QComboBox()
        self.wait_time = QLineEdit()
        self.deviation_time = QLineEdit()
        self.distribution_type_combo = QComboBox()
        self.toggle_action = QCheckBox()
        self.stacked_input_view = QStackedLayout()
        self.stacked_output_view = QStackedLayout()
        self.input_keyboard_subview = KeyboardWidgetView()
        self.input_mouse_subview = MouseWidgetView()
        self.output_keyboard_subview = KeyboardOutputWidgetView()
        self.output_mouse_subview = MouseOutputWidgetView()
        self.distribution_type_label = QLabel()
        self.input_subview_container.setLayout(self.stacked_input_view)
        self.output_subview_container.setLayout(self.stacked_output_view)
        self.start_button = QPushButton("Start")
        self.start_button.pressed.connect(self.submit)
        self.start_button.setDefault(True)
        self.input_subview_switch_combo.currentTextChanged.connect(self.switch_input_subview)
        self.distribution_type_combo.currentTextChanged.connect(self.switch_title)
        self.output_subview_switch_combo.currentTextChanged.connect(self.switch_output_subview)
        self.set_subview_items()
        self.set_combo_items()
        self.set_form(self.form_layout)
        self.set_validators()
        self.container.setLayout(self.form_layout)
        self.set_tooltips()
        self.setCentralWidget(self.container)
        self.load_defaults()

    def submit(self):
        self.hide()
        self.submit_view = SubmittedWindow(self)
        self.submit_view.run_info = self.get_init_info()
        self.submit_view.run_info.to_file(DEFAULTS_PATH)
        self.submit_view.run()

    def set_tooltips(self):
        self.wait_time.setToolTip("Minimum wait time (in seconds) between clicks.")
        self.deviation_time.setToolTip("Deviation time (in seconds) to wait between clicks.")
        self.toggle_action.setToolTip("Impacts if input toggles clicking, or if clicking persists while the input is " +
                                      "held.")
        self.input_keyboard_subview.alt_modifier.setToolTip("Impacts whether the left-alt key is used with input.")
        self.input_keyboard_subview.input_string.setToolTip("A whitespace-separated string of characters to watch " +
                                                            "for to start clicking.")

    def set_validators(self):
        self.output_keyboard_subview.hold_time.setValidator(QDoubleValidator(bottom=0.0))
        self.wait_time.setValidator(QDoubleValidator(bottom=0.0))
        self.deviation_time.setValidator(QDoubleValidator(bottom=0.0))
        self.input_keyboard_subview.input_string.setValidator(QRegExpValidator(QRegExp(r"([a-zA-Z0-9]\s)*")))
        self.output_keyboard_subview.input_sequence.setValidator(QRegExpValidator(QRegExp(r"([a-zA-Z0-9],)*")))

    def set_subview_items(self):
        self.stacked_input_view.addWidget(self.input_keyboard_subview)
        self.stacked_input_view.addWidget(self.input_mouse_subview)
        self.stacked_output_view.addWidget(self.output_keyboard_subview)
        self.stacked_output_view.addWidget(self.output_mouse_subview)

    def set_combo_items(self):
        self.input_subview_switch_combo.addItems(["Keyboard", "Mouse"])
        self.distribution_type_combo.addItems(["Uniform", "Gaussian"])
        self.output_subview_switch_combo.addItems(["Mouse", "Keyboard"])

    def set_form(self, form):
        form.addRow(QLabel("Wait time per click: "), self.wait_time)
        form.addRow(QLabel("Deviation distribution type: "), self.distribution_type_combo)
        form.addRow(self.distribution_type_label, self.deviation_time)
        form.addRow(QLabel("Toggle: "), self.toggle_action)
        form.addRow(QLabel("Input handling type: "), self.input_subview_switch_combo)
        form.addRow(self.input_subview_container)
        form.addRow(QLabel("Output handling type: "), self.output_subview_switch_combo)
        form.addRow(self.output_subview_container)
        form.addRow(self.start_button)

    def switch_input_subview(self):
        current_selection = self.input_subview_switch_combo.currentText()
        if current_selection == "Keyboard":
            self.stacked_input_view.setCurrentIndex(0)
        elif current_selection == "Mouse":
            self.stacked_input_view.setCurrentIndex(1)

    def switch_output_subview(self):
        current_selection = self.output_subview_switch_combo.currentText()
        if current_selection == "Keyboard":
            self.stacked_output_view.setCurrentIndex(0)
        elif current_selection == "Mouse":
            self.stacked_output_view.setCurrentIndex(1)

    def switch_title(self):
        current_selection = self.distribution_type_combo.currentText()
        if current_selection == "Uniform":
            self.distribution_type_label.setText("Randomized deviation: ")
        elif current_selection == "Gaussian":
            self.distribution_type_label.setText("Standard deviation: ")

    def get_init_info(self):
        def f(k, v):
            return {k: v} if v or v is False else {}
        conf_dict = {}
        conf_dict.update(f("wait_time", '' if not self.wait_time.text() else float(self.wait_time.text())))
        conf_dict.update(f("deviation_time",
                           '' if not self.deviation_time.text() else float(self.deviation_time.text())))
        conf_dict.update(f("distribution_type", self.distribution_type_combo.currentIndex()))
        conf_dict.update(f("toggle", self.toggle_action.isChecked()))
        conf_dict.update(f("input_mode", self.input_subview_switch_combo.currentIndex()))
        conf_dict.update(f("alt_modifier", self.input_keyboard_subview.alt_modifier.isChecked()))
        conf_dict.update(f("key_combination", self.input_keyboard_subview.input_string.text().strip().split()))
        conf_dict.update(f("special_mouse_press", self.input_mouse_subview.input_select.currentIndex()))
        conf_dict.update(f("output_type", self.output_subview_switch_combo.currentIndex()))
        conf_dict.update(f("output_sequence", list(self.output_keyboard_subview.input_sequence.text().replace(",", ''))))
        conf_dict.update(f("mouse_output", self.output_mouse_subview.output_selector.currentIndex()))
        conf_dict.update(f("hold_time", '' if not self.output_keyboard_subview.hold_time.text() else
                           float(self.output_keyboard_subview.hold_time.text())))
        return Config(**conf_dict)

    def load_defaults(self):
        self.wait_time.setText(float_to_str(self.defaults.wait_time))
        self.deviation_time.setText(float_to_str(self.defaults.deviation_time))
        self.distribution_type_combo.setCurrentIndex(self.defaults.distribution_type)
        self.toggle_action.setChecked(self.defaults.toggle)
        self.input_subview_switch_combo.setCurrentIndex(self.defaults.input_mode)
        self.stacked_input_view.setCurrentIndex(self.defaults.input_mode)
        self.input_keyboard_subview.alt_modifier.setChecked(self.defaults.alt_modifier)
        self.input_keyboard_subview.input_string.setText(" ".join(self.defaults.key_combination))
        self.input_mouse_subview.input_select.setCurrentIndex(self.defaults.special_mouse_press)
        self.output_subview_switch_combo.setCurrentIndex(self.defaults.output_type)
        self.output_mouse_subview.output_selector.setCurrentIndex(self.defaults.mouse_output)
        self.output_keyboard_subview.input_sequence.setText(",".join(self.defaults.output_sequence))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
