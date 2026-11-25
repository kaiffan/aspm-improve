# AD/LDAP group mapping

AD/LDAP federation is configured at Keycloak. ASPM only talks to Keycloak's OIDC realm.

For each approved group, assign a UUID-named client role under a dedicated entitlements client. Use Keycloak's built-in client-role mapper to emit these entitlements into the ID token as a multivalued claim. A role mapping on a Keycloak group or its federated counterpart carries the opaque identifier even when display paths change. Keycloak administrators own group-to-entitlement assignment.

In ASPM SSO access mappings, associate the entitlement ID with an existing Product ID. User sessions receive the union of active Product mappings. A user with no matching mappings sees an empty portfolio. Group and Project display strings are presentation labels. Removal of the ASPM mapping applies on the subsequent request. An IdP membership change takes effect within the claim freshness window, subject to federation propagation on the IdP side.

The synthetic realm pairs devsecops-TEST-user and devsecops-PAYMENTS-user with separate UUIDs. Its result applies to the local Keycloak realm. Corporate directory federation, nested group behavior and sync timing still need pilot evidence.
