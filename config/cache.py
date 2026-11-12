"""Redis kesh: Redis yiqilsa ham API ishlashda davom etadi (kesh shunchaki o'tkazib yuboriladi)."""
import logging

from django.core.cache import cache
from django.core.cache.backends.redis import RedisCache
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

logger = logging.getLogger(__name__)
_XATO = (RedisConnectionError, RedisTimeoutError, OSError)


def _xavfsiz(nom, default):
    def wrapper(self, *args, **kwargs):
        try:
            return getattr(super(SafeRedisCache, self), nom)(*args, **kwargs)
        except _XATO:
            logger.warning("Redis keshi mavjud emas (%s)", nom)
            return default

    wrapper.__name__ = nom
    return wrapper


class SafeRedisCache(RedisCache):
    get = _xavfsiz("get", None)
    set = _xavfsiz("set", None)
    add = _xavfsiz("add", False)
    delete = _xavfsiz("delete", False)
    get_many = _xavfsiz("get_many", {})
    touch = _xavfsiz("touch", False)
    has_key = _xavfsiz("has_key", False)


STATS_VERSION_KEY = "stats:version"


def stats_versiyasi() -> int:
    return cache.get(STATS_VERSION_KEY, 1)


def stats_keshini_tozala() -> None:
    """Ma'lumot o'zgarganda barcha statistika kalitlari bir zumda eskiradi."""
    try:
        cache.incr(STATS_VERSION_KEY)
    except ValueError:
        cache.set(STATS_VERSION_KEY, 2, None)
    except _XATO:
        pass
