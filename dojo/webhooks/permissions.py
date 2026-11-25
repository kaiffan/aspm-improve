def can_manage_webhooks(user):
    """Platform capability, deliberately independent of Product membership and is_staff."""
    return bool(user and user.is_authenticated and user.is_active and (
        user.is_superuser or user.has_perm("dojo.manage_outbound_webhooks")
    ))
