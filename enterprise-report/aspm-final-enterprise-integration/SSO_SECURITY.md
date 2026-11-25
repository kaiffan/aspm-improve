# SSO security and session expiry

The browser starts an authorization request with a one-use session flow, independent random state and nonce, and a PKCE S256 challenge. The server exchanges the code over verified TLS and uses PyJWT to validate a fixed RS256 algorithm and matching Keycloak RSA key, signature, issuer, audience, authorized party, expiry and nonce. The callback rotates the session key and the CSRF secret. Redirect destinations use same-site relative paths.

Users are linked by issuer and subject. Local email addresses do not participate in account matching. Managed accounts have an unusable password and no Django staff or superuser flag. Legacy Django tokens and ASPM machine-token issuance reject those identities.

The default claim freshness window is 300 seconds and the configurable maximum is 600. Access can expire sooner at ID token expiry, application session expiry, local deactivation or removal of an ASPM Product mapping. At the freshness deadline subsequent requests fail closed and the user signs in again. The next authorization-code exchange obtains current Keycloak claims. A temporary outage allows an already-valid session until its freshness or expiry deadline. It cannot extend the deadline.

Logout uses CSRF-protected POST. With provider logout enabled the already-cleared ASPM session redirects to Keycloak with the registered callback. Authentication callback query strings must be excluded from proxy and application access logs. No Keycloak or CI secret is included in a webhook.

The outage test kept a previously valid session usable until its configured expiry and then returned HTTP 403 while the provider remained down. [Raw outage evidence](raw/keycloak-outage.json)
