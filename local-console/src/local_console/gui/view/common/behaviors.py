# Copyright 2024 Sony Semiconductor Solutions Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This file incorporates material from the KivyMD project, which is licensed
# under the MIT License:
#
#     MIT License
#
#     Copyright (c) 2024 KivyMD contributors
#
#     Permission is hereby granted, free of charge, to any person obtaining a copy
#     of this software and associated documentation files (the "Software"), to deal
#     in the Software without restriction, including without limitation the rights
#     to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#     copies of the Software, and to permit persons to whom the Software is
#     furnished to do so, subject to the following conditions:
#
#     The above copyright notice and this permission notice shall be included in all
#     copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#     SOFTWARE.
#
# The following modifications have been made to the original KivyMD code:
#
# - Instead of dispatching on_enter only once during the crossing of the cursor
#   into the widget, this behavior dispatches on_enter for every position that
#   the cursor has as long as it is inside the widget.
#
# SPDX-License-Identifier: Apache-2.0


__all__ = ("HoverBehavior",)

from typing import Any

from kivy.core.window import Window
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget


class HoverBehavior(Widget):
    """
    :Events:
        :attr:`on_enter`
            Fired when mouse enters the bbox of the widget and the widget is
            visible.
        :attr:`on_leave`
            Fired when the mouse exits the widget and the widget is visible.
    """

    hovering = BooleanProperty(False)
    """
    `True`, if the mouse cursor is within the borders of the widget.

    Note that this is set and cleared even if the widget is not visible.

    :attr:`hover` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    hover_visible = BooleanProperty(False)
    """
    `True` if hovering is `True` and is the current widget is visible.

    :attr:`hover_visible` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    current_point = ObjectProperty(allownone=True)
    """
    Holds the current position where the mouse pointer is within the Widget
    if the Widget is visible and is currently in a hovering state.

    :attr:`enter_point` is a :class:`~kivy.properties.ObjectProperty`
    and defaults to `None`.
    """

    detect_visible = BooleanProperty(True)
    """
    Should this widget perform the visibility check?

    :attr:`detect_visible` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to  `True`.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.register_event_type("on_enter")
        self.register_event_type("on_leave")
        Window.bind(mouse_pos=self.on_mouse_update)
        super().__init__(*args, **kwargs)

    def on_mouse_update(self, window: Window, pos: tuple[int, int]) -> None:
        #  If the Widget currently has no parent, do nothing.
        if not self.get_root_window():
            return

        # Is the pointer in the same position as the widget?
        # If not - then issue an on_exit event if needed.
        if not self.collide_point(
            *self.to_widget(*pos)
            if not isinstance(self, RelativeLayout)
            else (pos[0], pos[1])
        ):
            self.hovering = False
            self.current_point = None
            if self.hover_visible:
                self.hover_visible = False
                self.dispatch("on_leave")
            return

        # Now set the hovering attribute
        self.hovering = True

        # We need to traverse the tree to see if the Widget is visible.
        # This is a two stage process - first go up the tree to the root.
        # Window. At each stage - check that the Widget is actually visible.
        # Second - at the root Window check that there is not another branch
        # covering the Widget.
        self.hover_visible = True

        if self.detect_visible:
            widget: Widget = self
            while True:
                # Walk up the Widget tree from the target Widget.
                parent = widget.parent
                try:
                    # See if the mouse point collides with the parent
                    # using both local and global coordinates to cover absolute
                    # and relative layouts.
                    pinside = parent.collide_point(
                        *parent.to_widget(*pos)
                    ) or parent.collide_point(*pos)
                except Exception:
                    # The collide_point will error when you reach the root
                    # Window.
                    break
                if not pinside:
                    self.hover_visible = False
                    break
                # Iterate upwards.
                widget = parent

            #  parent = root window
            #  widget = first Widget on the current branch
            children = parent.children
            for child in children:
                # For each top level widget - check if is current branch.
                # If it is - then break.
                # If not then - since we start at 0 - this widget is visible.
                # Check to see if it should take the hover.
                if child == widget:
                    # This means that the current widget is visible.
                    break
                if child.collide_point(*pos):
                    # This means that the current widget is covered by a modal
                    # or popup.
                    self.hover_visible = False
                    break

        if self.hover_visible:
            self.current_point = pos
            self.dispatch("on_enter")

    def on_enter(self) -> None:
        """Fired when mouse enter the bbox of the widget."""

    def on_leave(self) -> None:
        """Fired when the mouse goes outside the widget border."""
