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
# SPDX-License-Identifier: Apache-2.0
from typing import Generic
from typing import Optional
from typing import TypeVar

T = TypeVar("T")


class TrackingVariable(Generic[T]):
    """
    This class implements a variable that exposes .previous
    property for getting the previous value assigned to it.
    For the current value, read and assignment works as usual
    """

    def __init__(self, initial_value: Optional[T] = None) -> None:
        self.current_value: Optional[T] = initial_value
        self.previous_value: Optional[T] = None

    @property
    def value(self) -> Optional[T]:
        """Get the current value of the variable."""
        return self.current_value

    @value.setter
    def value(self, new_value: T) -> None:
        """Set a new value for the variable, updating the previous value."""
        self.previous_value = self.current_value
        self.current_value = new_value

    @property
    def previous(self) -> Optional[T]:
        """Get the previous value of the variable."""
        return self.previous_value

    def __repr__(self) -> str:
        return f"Current Value: {self.current_value}, Previous Value: {self.previous_value}"
