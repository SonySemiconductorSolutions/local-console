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
import io

import qrcode
from kivy.core.image import Image as CoreImage
from kivy.core.image import Texture

# Color tuple, whose components value range is [0, 255]
Color = tuple[int, ...]


def qr_object_as_texture(
    qr: qrcode.main.QRCode, background_color: Color, fill_color: Color
) -> Texture:
    """
    This function renders a QR code as a Kivy texture, so that an uix.Image widget
    can be updated without involving the filesystem
    :param qr: QR code object
    :param background_color: Background (i.e. space between cells) color for the QR code
    :param fill_color: Foreground (i.e. cell) color for the QR code
    :return: object that can be assigned to the .texture property of a kivy.uix.Image object
    """
    img = qr.make_image(fill_color=fill_color, back_color=background_color)
    img_data = io.BytesIO()
    img_ext = "PNG"
    img.save(img_data, format=img_ext)
    img_data.seek(0)
    cim = CoreImage(img_data, ext=img_ext.lower())
    return cim.texture
