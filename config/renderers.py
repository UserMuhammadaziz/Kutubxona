from rest_framework.renderers import JSONRenderer


class StatusJSONRenderer(JSONRenderer):
    """Adds a boolean `status` (true = success, false = error) to every JSON object response.

    Lists and responses that already have a `status` field (e.g. organization
    `status`) are left untouched so existing clients keep working.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        if response is not None and isinstance(data, dict) and "status" not in data:
            data = {"status": response.status_code < 400, **data}
        return super().render(data, accepted_media_type, renderer_context)
