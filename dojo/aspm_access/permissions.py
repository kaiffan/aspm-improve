from dojo.aspm_access.models import SsoProductGrant

TRIAGE_FIELDS = frozenset({"active", "verified", "false_p", "out_of_scope", "is_mitigated"})

SECOPS_CAPABILITIES = {
    "dojo.manage_engagement_policy",
    "dojo.manage_outbound_webhooks",
    "dojo.manage_sso_mapping",
    "dojo.change_system_settings",
    "dojo.view_system_settings",
}


def principal(user):
    if user is not None and getattr(user, "is_active", False):
        return getattr(user, "_aspm_principal", None)
    return None


def role(user):
    identity = principal(user)
    return identity["role"] if identity is not None else None


def has_capability(user, permission):
    if not user.is_authenticated or not user.is_active:
        return False
    access = role(user)
    if access is not None:
        return access == "secops" and permission in SECOPS_CAPABILITIES
    return user.has_perm(permission)


def granted_product_ids(user):
    identity = principal(user)
    return SsoProductGrant.objects.filter(
        issuer=identity["issuer"], group_id__in=identity["groups"],
    ).order_by().values("product_id")
