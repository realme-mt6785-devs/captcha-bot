# SPDX-FileCopyrightText: 2026 Firdaus Hakimi <hakimifirdaus944@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os

from jsondb.database import JsonDB

from captcha_bot import custom_logger  # noqa: F401

PERSIST_DIR = os.getenv("PERSIST_DIR") or "/persist/storage"
CHAT_WHITELIST: list[int] = [
    -1001267207006,  # photography group
    -1002237651092,  # disc
    -1001754321934,  # community
    -1001309495065,  # r6
    -1001955516964,  # ansh
]
TIMEOUT_SECONDS = 60
TEMP_BAN_SECONDS = 21600
MAX_FAIL_BEFORE_TEMPBAN = 6
DELETE_SECONDS = 30
FAIL_COUNT_COOLDOWN_TIME = 86400
FAIL_COUNT_SWEEPER_CHAT_ID = -1001299514785

db = JsonDB(__name__, PERSIST_DIR)
