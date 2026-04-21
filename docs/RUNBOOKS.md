# Runbooks

Admin procedures for running Terramedic in production. Each section
is self-contained: pre-requisites, steps, verification. For the
system architecture behind these procedures, see
[ARCHITECTURE.md](ARCHITECTURE.md).

## Re-evaluating organizations after a prompt-version bump

When `curation.prompt.PROMPT_VERSION` changes, existing
`OrganizationEvaluation` rows stay frozen at the old version — their
stored `evaluation_data.prompt_version` does not update
automatically. Re-running them against the new prompt is a
three-step procedure that splits work between your local machine
(authenticated to the `claude` CLI, no VPC access to the dev RDS)
and the Lambda environment (inside the VPC, no `claude` binary).

### When to run

- After merging a PR that bumps `PROMPT_VERSION`, when you want the
  existing evaluation pool to reflect the new criteria.
- Most common scenario: the new prompt tightens a criterion and
  some previously-rejected orgs should get another look. The
  default `--status rejected` below targets exactly that pool.

### Pre-requisites

- Logged in to the `claude` CLI on your local machine (`claude
  auth`). The fixture-generation step shells out to it.
- AWS credentials for the target stage available via `aws-vault`
  (or whatever wrapper your workstation uses). The commands that
  call `zappa` need creds for the stage's account.

### Steps

1. **List the candidate URLs from the dev DB.**

   ```bash
   aws-vault exec terramedic-dev -- \
     poetry run zappa manage dev \
     "list_reevaluation_candidates" > urls.txt
   ```

   Prints URLs of evaluations whose stored `prompt_version` lags the
   current one. `--status` selects which review states to include:

   - `rejected` (default) — revisit rejections that may have been
     driven by the old prompt's weaknesses.
   - `approved` — re-run live orgs if the prompt change should
     propagate to their descriptions or categories.
   - `pending` — supersede still-unreviewed evaluations.
   - `all` — every evaluation behind the current version.

   Pass `--status` inside the quoted command:

   ```bash
   aws-vault exec terramedic-dev -- \
     poetry run zappa manage dev \
     "list_reevaluation_candidates --status all" > urls.txt
   ```

2. **Evaluate locally via claude-code and write a fixture.** No
   AWS creds needed — this step runs entirely on your machine:

   ```bash
   poetry run python manage.py evaluate_urls_to_fixtures \
     urls.txt --out reeval.json
   ```

   The command shells out to `evaluate_org_via_claude_code` for
   each URL, tolerates per-URL failures (logs and continues), and
   writes a single Django fixture file. Blank lines and `#`
   comments in `urls.txt` are ignored.

   Preview first if the URL list is long:

   ```bash
   poetry run python manage.py evaluate_urls_to_fixtures \
     urls.txt --dry-run
   ```

3. **Push the fixture into the target stage without redeploying.**

   ```bash
   aws-vault exec terramedic-dev -- \
     poetry run python manage.py zappa_loaddata dev reeval.json
   ```

   Base64-encodes the fixture and hands it to `zappa invoke --raw`,
   which decodes it and pipes it into Django's `loaddata` over
   stdin. The 6 MB Lambda sync-invoke payload limit applies to the
   full snippet going on the wire — since base64 expands content
   ~33%, the command refuses fixtures whose encoded payload would
   exceed the limit (~4 MB raw in practice) and suggests uploading
   to S3 instead.

### Verification

- The new rows appear in the admin evaluation queue at
  `/admin/organizations/organizationevaluation/?status__exact=pending`.
- Spot-check one: open the detail page, confirm `prompt_version`
  in the raw data matches the current `PROMPT_VERSION`, and that
  the categories / description reflect the updated prompt.
- Approving a new row creates a fresh `Organization` via the
  `create_org_on_approval` signal. If the URL already has a
  live `Organization` from the prior evaluation, both will exist
  — deactivate the old one manually (`is_active = False`) once
  you're satisfied with the new evaluation.

### Troubleshooting

- **`list_reevaluation_candidates` prints nothing.** Every eval
  in the selected status pool is already at the current
  `PROMPT_VERSION`. Try `--status all` or confirm the prompt
  version actually changed.
- **`evaluate_urls_to_fixtures` reports FAILED for some URLs.**
  Usually either the `claude` CLI session expired (`claude auth`
  to refresh) or the org's website is unreachable. Re-run the
  command against a filtered URL list — it's idempotent at the
  fixture-write level (each run writes its own file).
- **`zappa_loaddata` fails with "too large".** Split the fixture
  into chunks by URL and run the command per chunk, or upload
  the fixture to S3 and load from there with a small wrapper.
