# SPDX-FileCopyrightText: 2026 Firdaus Hakimi <hakimifirdaus944@gmail.com>
# SPDX-License-Identifier: Apache-2.0
import logging
from dataclasses import asdict, dataclass, field

from captcha_bot import db

logger = logging.getLogger(__name__)

type UserIdKey = str
type ChatIdKey = str


@dataclass(slots=True)
class UserRecord:
    expected: int
    challenge_message_id: int
    expires_at: float


@dataclass(slots=True)
class DeleterRecord:
    delete_at: float


@dataclass(slots=True)
class FailureBucket:
    failures: dict[UserIdKey, int] = field(default_factory=dict)


def get_and_create_deleter_record(
    chat_id: int | str,
    message_id: int | str,
    *,
    create: bool = False,
    delete_at: float = 0,
) -> DeleterRecord | None:
    chat_key = str(chat_id)
    message_key = str(message_id)
    chat = db.data.get(chat_key)

    if chat is None:
        if not create:
            return None
        db.data[chat_key] = {}
        chat = db.data[chat_key]

    deleter = chat.get("deleter")
    if deleter is None:
        if not create:
            return None
        chat["deleter"] = {}
        deleter = chat["deleter"]

    message = deleter.get(message_key)
    if message is None:
        if not create:
            return None
        deleter[message_key] = {"delete_at": delete_at}

    return DeleterRecord(**deleter[message_key])


def delete_deleter_record(chat_id: int, message_id: int) -> None:
    chat_key = str(chat_id)
    message_key = str(message_id)

    chat = db.data.get(chat_key)
    if chat is None:
        return

    deleter = chat.get("deleter")
    if deleter is None:
        return

    message = deleter.get(message_key)
    if message is None:
        return

    deleter.pop(message_key, None)


def get_failures_bucket(chat_id: int, *, create: bool = False) -> FailureBucket | None:
    chat_key = str(chat_id)
    chat = db.data.get(chat_key)

    if chat is None:
        if not create:
            return None
        db.data[chat_key] = {}
        chat = db.data[chat_key]

    failures = chat.get("failures")
    if failures is None:
        if not create:
            return None
        chat["failures"] = {}
        failures = chat["failures"]

    return FailureBucket(failures)


def increment_consecutive_failures(chat_id: int, user_id: int) -> int:
    failure_bucket = get_failures_bucket(chat_id, create=True)
    assert failure_bucket is not None

    user_key = str(user_id)
    failure_bucket.failures[user_key] = int(failure_bucket.failures.get(user_key, 0)) + 1

    logger.info(
        "Incremented consecutive failures to %d for user %d in chat %d",
        failure_bucket.failures[user_key],
        user_id,
        chat_id,
    )

    return failure_bucket.failures[user_key]


def reset_consecutive_failures(chat_id: int, user_id: int) -> None:
    failure_bucket = get_failures_bucket(chat_id)
    if failure_bucket is None:
        logger.warning(
            "cannot reset consecutive failures for user %d in chat %d, failed to get failure bucket",
            user_id,
            chat_id,
        )
        return

    failure_bucket.failures.pop(str(user_id), None)


def get_user_record(chat_id: int, user_id: int) -> UserRecord | None:
    try:
        user_record = UserRecord(**db.data.get(str(chat_id), {}).get(str(user_id)))
    except TypeError:
        user_record = None

    return user_record


def save_user_record(chat_id: int, user_id: int, user_record: UserRecord) -> None:
    chat_key = str(chat_id)
    user_key = str(user_id)

    if chat_key not in db.data:
        db.data[chat_key] = {}

    db.data[chat_key][user_key] = asdict(user_record)

    logger.info(
        "saved captcha record for user %d in chat %d (challenge_message_id=%d, expires_at=%.3f)",
        user_id,
        chat_id,
        user_record.challenge_message_id,
        user_record.expires_at,
    )


def delete_user_record(chat_id: int, user_id: int) -> None:
    chat_key = str(chat_id)
    user_key = str(user_id)

    chat = db.data.get(chat_key)
    if not chat:
        return

    chat.pop(user_key, None)
    if not chat:
        db.data.pop(chat_key, None)

    logger.info(
        "deleted captcha record for user %d in chat %d",
        user_id,
        chat_id,
    )
