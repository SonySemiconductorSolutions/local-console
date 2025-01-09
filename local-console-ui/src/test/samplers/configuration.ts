/**
 * Copyright 2024 Sony Semiconductor Solutions Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { Configuration, OperationMode } from '@app/core/device/configuration';

export namespace Configurations {
  export function sample(type: OperationMode = 'classification') {
    return <Configuration>{
      image_dir_path: 'config/images/path',
      inference_dir_path: 'config/inferences/long/very/long/super/long/path',
      size: 10,
      unit: 'Mb',
      vapp_type: type,
    };
  }
}
