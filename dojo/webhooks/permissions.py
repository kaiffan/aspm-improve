from dojo.aspm_access.permissions import has_capability


def can_manage_webhooks(user):
    """Platform capability, deliberately independent of Product membership and is_staff."""
    return bool(user and user.is_authenticated and user.is_active and (
        has_capability(user, "dojo.manage_outbound_webhooks")
    ))
