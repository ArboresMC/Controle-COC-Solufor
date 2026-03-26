from django.core.cache import cache


def _scope_key(scope_type, scope_id=None):
    return f"{scope_type}:{scope_id or 'all'}"


def get_scope_version(scope_type, scope_id=None):
    key = f"perf_version:{_scope_key(scope_type, scope_id)}"
    version = cache.get(key)
    if version is None:
        version = 1
        cache.set(key, version, None)
    return version


def bump_scope_version(scope_type, scope_id=None):
    key = f"perf_version:{_scope_key(scope_type, scope_id)}"
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 2, None)


def build_cache_key(prefix, scope_type, scope_id=None, extra=None):
    version = get_scope_version(scope_type, scope_id)
    suffix = f":{extra}" if extra else ''
    return f"{prefix}:{_scope_key(scope_type, scope_id)}:v{version}{suffix}"


def invalidate_for_participant(participant_id=None, organization_id=None):
    if participant_id:
        bump_scope_version('participant', participant_id)
    if organization_id:
        bump_scope_version('organization', organization_id)
