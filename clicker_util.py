from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Listener as KeyboardListener
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Listener as MouseListener
from threading import Thread, Event
import time
import json
from typing import List
import numpy as np
import random
import os


def from_file(file_path: str):
    if os.path.exists(file_path):
        return Config(**json.load(open(file_path, 'r')))
    else:
        return Config()


class Config:
    def __init__(self, **kwargs):
        """Defines default behavior for AutoClickerThread.

        :keyword wait_time: Base time to wait between clicks in seconds. (float)

        :keyword deviation_time: Amount of time to randomly deviate between clicks in seconds. (float)

        :keyword distribution_type: Kind of distribution to use for randomized deviation time. `0` for uniform, `1` for normal. (int)

        :keyword toggle: Toggle clicking based on input. (bool)

        :keyword input_mode: Use keyboard or mouse for input. `0` for keyboard, `1` for mouse. (int)

        :keyword alt_modifier: Use an alt modifier for keyboard input. (bool)

        :keyword key_combination: Characters to use for keyboard hotkey. (List[char])

        :keyword special_mouse_press: Use special mouse key for input. (int)

        :keyword output_type: Specifies whether mouse or keyboard for output.

        :keyword output_sequence: Specifies what sequence to repeat on keyboard for input.

        :keyword mouse_output: Specifies which button to push on mouse for input.

        :keyword hold_time: Defines hold time for keyboard keys.
        """
        self.wait_time: float = kwargs.get("wait_time", 0.)
        self.deviation_time: float = kwargs.get("deviation_time", 0.0)
        self.distribution_type: int = kwargs.get("distribution_type", 0)
        self.toggle: bool = kwargs.get("toggle", False)
        self.input_mode: int = kwargs.get("input_mode", 0)
        self.alt_modifier: bool = kwargs.get("alt_modifier", False)
        self.key_combination: List[chr] = kwargs.get("key_combination", [])
        self.special_mouse_press: int = kwargs.get("special_mouse_press", 0)
        self.output_type: int = kwargs.get("output_type", 0)
        self.output_sequence: List[chr] = kwargs.get("output_sequence", [])
        self.mouse_output: int = kwargs.get("mouse_output", 0)
        self.hold_time: float = kwargs.get("hold_time", 0.0)

    def to_file(self, file_path):
        json.dump(self.__dict__, open(file_path, 'w'), indent=1)


class AutoClickerThread(Thread):
    def __init__(self, parent_ui=None, config=Config()):
        super(AutoClickerThread, self).__init__()
        self.ui = parent_ui
        self.config = config
        self.thread = None
        self._stop_event = Event()
        self.mouse_button = None
        self.current_keys = set()
        self.accepted_keys = set()
        self.reload_config()
        self.activated = False
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        self.last_state = False
        self.sequence_index = 0
        self.sequence_length = len(self.config.output_sequence)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        self.thread.start()
        while not self.stopped():
            if self.activated:
                if self.config.output_type == 0 and self.config.output_sequence:
                    # Mouse output
                    to_press = Button.right if self.config.mouse_output == 1 else Button.left
                    self.mouse_controller.press(to_press)
                    self.mouse_controller.release(to_press)
                elif self.config.output_type == 1:
                    # Keyboard output
                    current_key = self.config.output_sequence[self.sequence_index]
                    to_press = KeyCode.from_char(current_key)
                    self.keyboard_controller.press(to_press)
                    time.sleep(self.config.hold_time)
                    self.keyboard_controller.release(to_press)
                    self.sequence_index = (self.sequence_index + 1) % self.sequence_length
            if self.config.distribution_type == 0:
                time.sleep(self.config.wait_time + random.uniform(0, self.config.deviation_time))
            else:
                time.sleep(abs(np.random.normal(loc=self.config.wait_time, scale=self.config.deviation_time)))
            self.last_state = self.activated
        self.thread.stop()

    def set_activated(self, value):
        if self.ui:
            self.ui.update_clicking(value)
        self.activated = value

    def on_press(self, key):
        if key in self.accepted_keys:
            self.current_keys.add(key)
            if self.accepted_keys.issubset(self.current_keys):
                if self.config.toggle:
                    self.set_activated(not self.activated)
                else:
                    self.set_activated(True)

    def on_click(self, x, y, button, pressed):
        if button == self.mouse_button:
            if self.config.toggle and pressed:
                self.set_activated(not self.activated)
            elif not self.config.toggle and pressed:
                self.set_activated(True)
            elif not self.config.toggle and not pressed:
                self.set_activated(False)

    def on_release(self, key):
        try:
            if key in self.accepted_keys:
                if not self.config.toggle:
                    self.set_activated(False)
                self.current_keys.remove(key)
        except KeyError:
            pass

    def set_config(self, config):
        self.config = config
        self.reload_config()

    def reload_config(self):
        self.accepted_keys = set()
        if self.config.alt_modifier:
            self.accepted_keys.add(Key.alt_l)
        for key in self.config.key_combination:
            self.accepted_keys.add(KeyCode.from_char(key))
        self.thread = {0: KeyboardListener(on_press=self.on_press, on_release=self.on_release),
                       1: MouseListener(on_click=self.on_click)}.get(self.config.input_mode)
        self.mouse_button = {0: Button.x1,
                             1: Button.x2}.get(self.config.special_mouse_press)
        self.sequence_length = len(self.config.output_sequence)
