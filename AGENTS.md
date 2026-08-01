# Repository instructions

## GitHub authentication

- Treat `gh auth status` results obtained inside the restricted sandbox as inconclusive. Network restrictions can make a valid keyring token appear invalid.
- Before telling the user that GitHub authentication has expired or asking them to run `gh auth login`, rerun `gh auth status` with escalated/network-enabled permissions.
- Ask the user to authenticate again only when the escalated `gh auth status` also fails.
- Do not start a second device-activation flow merely because the sandboxed check reported an invalid token.
- Run GitHub network operations such as `git fetch`, `git push`, and `gh` API calls with the required escalated/network-enabled permissions.
