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

import { HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ReplaySubject } from 'rxjs';
import { EnvService } from '../common/environment.service';
import { HttpApiClient } from '../common/http/http';
import {
  DeployConfigApplyIn,
  DeployConfigApplyOut,
  DeployConfigsIn,
  DeployHistoriesOut,
  DeployHistoryOut,
} from './deployment';

@Injectable({
  providedIn: 'root',
})
export class DeploymentService {
  private deploymentSubject = new ReplaySubject<DeployHistoriesOut>(1);
  private defaultLimit: number = 256;
  public deployment$ = this.deploymentSubject.asObservable();

  constructor(
    private http: HttpApiClient,
    private envService: EnvService,
  ) {}

  get deployConfigurationV2Path() {
    return `${this.envService.getApiUrl()}/deploy_configs`;
  }

  get deployHistoryPathV2() {
    return `${this.envService.getApiUrl()}/deploy_history`;
  }

  createDeploymentConfigV2(payload: DeployConfigsIn) {
    return this.http.post(this.deployConfigurationV2Path, payload);
  }

  deployByConfigurationV2(configId: string, payload: DeployConfigApplyIn) {
    const url = `${this.deployConfigurationV2Path}/${configId}/apply`;
    return this.http.post<DeployConfigApplyOut>(url, payload, false);
  }

  getDeployStatusV2(deploy_id: string) {
    return this.http.get<DeployHistoryOut>(
      `${this.deployHistoryPathV2}/${deploy_id}`,
    );
  }

  async getDeploymentsStatusV2() {
    // NOTE: Assumes number of elements to fetch are always lower than limit
    let queryParams = new HttpParams();
    queryParams = queryParams.append('limit', this.defaultLimit);
    return this.http.get<DeployHistoriesOut>(
      `${this.deployHistoryPathV2}`,
      (queryParams = queryParams),
    );
  }

  async loadDeployments() {
    try {
      this.deploymentSubject.next(await this.getDeploymentsStatusV2());
    } catch (err) {
      console.error('Could not update deployment list', err);
    }
  }
}
