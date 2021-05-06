"""
Copyright (c) 2021 Heureka Group a.s. All Rights Reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import json as _json


def bool_like(val):
    return str(val).lower() not in ('false', '0', 'no', 'off', 'disable', 'disabled', '')


def json(val):
    """
    A convenient converter that JSON-deserializes strings.
    """
    return _json.loads(val, encoding='utf-8')
