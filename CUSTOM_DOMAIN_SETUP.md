# BTGEntity.io custom-domain handoff

The public ENTITY website is deliberately built with relative internal URLs so it can move from the current GitHub Pages project URL to a custom domain without restructuring the site.

## Intended domain

Preferred fallback domain: `BTGEntity.io`

Do not add a `CNAME` file or change canonical URLs until BTG has actually registered and controls the domain.

## Safe activation sequence

1. Register `BTGEntity.io` through the chosen registrar.
2. Verify the custom domain for the Blackmore Technology Group GitHub organization/account before delegating DNS, where available.
3. In `blackmore-technology-group/ENTITY-DOCS` → Settings → Pages, set the custom domain to `BTGEntity.io` (or `www.BTGEntity.io` if that is chosen as canonical).
4. Configure DNS at the registrar/provider.
5. Verify DNS resolution.
6. Enable/enforce HTTPS after GitHub provisions the certificate.
7. Add/update the Pages `CNAME` file only through the supported Pages flow or repository source as appropriate.
8. Replace GitHub Pages canonical/OG/sitemap URLs with the final `https://BTGEntity.io/` URLs in one controlled change.
9. Keep the GitHub repositories as the source/evidence backend. Do not redirect repository URLs away from GitHub.

## GitHub Pages DNS values (current GitHub documentation)

For an apex domain using A records:

- `185.199.108.153`
- `185.199.109.153`
- `185.199.110.153`
- `185.199.111.153`

For IPv6 AAAA support:

- `2606:50c0:8000::153`
- `2606:50c0:8001::153`
- `2606:50c0:8002::153`
- `2606:50c0:8003::153`

For `www`, use a CNAME pointing to the organization Pages hostname:

`blackmore-technology-group.github.io`

GitHub recommends configuring both an apex and `www` variant and supports automatic redirects between the correctly configured variants.

## Security notes

- Do not create wildcard DNS records for the domain.
- Do not point DNS to GitHub before adding/verifying the custom domain in GitHub Pages.
- Recheck the official GitHub Pages documentation at activation time because DNS guidance can change.
- Keep the current GitHub Pages URL available during DNS propagation.

Official source reviewed 2026-09-28:
https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
