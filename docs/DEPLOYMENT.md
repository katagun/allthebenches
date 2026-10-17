# Deploying allthebenches.com

Repository: https://github.com/katagun/allthebenches

The committed Pages workflow builds `web/dist` at base path `/` and deploys it using GitHub Actions. `web/public/CNAME` records `allthebenches.com` and is copied into the build. For Actions deployments, the file alone does not configure the domain: set it in repository Pages settings too.

## First publication

1. Create the public repository and push the reviewed project to `main`. Review the files before the first push; ignored local caches and credentials must remain private.
2. In repository **Settings → Pages**, choose **GitHub Actions** as the build source.
3. Verify domain ownership in the GitHub account's Pages settings using the TXT record GitHub supplies. Retain that record.
4. Set the repository Pages custom domain to `allthebenches.com` before pointing DNS at GitHub.
5. At the DNS provider, configure these records (remove conflicting parking/forwarding records for these hosts, preserving unrelated mail/TXT records):

| Type | Name | Value |
| --- | --- | --- |
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | katagun.github.io |

Optional IPv6: add apex AAAA records `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, and `2606:50c0:8003::153`. Do not use wildcard records. The `www` CNAME targets the GitHub account hostname, without a repository path.

6. Run **Deploy GitHub Pages** or push to `main`. The build job must pass before deployment; fork PRs only run checks.
7. Once GitHub's DNS check and certificate provisioning finish, enable **Enforce HTTPS**. Propagation/certificate issuance may take time.
8. Verify the apex and `www` redirect, favicon, model icons, five `/data/*.json` files, worker loading, preset switching, shared URLs, evidence links and CSV export. Test Firefox and a narrow viewport.

These instructions follow [GitHub's custom-domain documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) and [domain verification guide](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages). DNS and account settings are external to this repository.

## Build and rollback

```sh
pnpm check
VITE_BASE_PATH=/ pnpm --dir web build
pnpm --dir web preview --host 127.0.0.1
```

No upstream secrets are required for deployment. `OPENROUTER_API_KEY` is optional for the separate metadata staging workflow. Only the deploy job has `pages: write` and `id-token: write`; the build job has read-only repository access.

To roll back, revert the bad change on `main` and deploy the resulting commit. Preserve stable IDs and URL-state compatibility. A domain change also requires changing Pages settings, DNS, this guide and `web/public/CNAME`.
