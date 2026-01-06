# ConsumerThread is defined in producer.py to share BaseControlledThread logic.
# This file exists to match the required structure; it re-exports ConsumerThread.
from threads.producer import ConsumerThread  # noqa: F401
