# Day 9 — Notes
## Week 3, Wednesday: AWS Deployment, Frontend React Deployment, Backend AWS Lambda, Frontend AWS S3/CloudWatch

---

## Executive Summary

Every prior day built or tested something in isolation. Today, for
the first time, the entire RoboPulse stack went live, end-to-end, in
the cloud: React served through CloudFront and S3, FastAPI running
inside AWS Lambda (replacing the problem statement's original App
Runner, per the Day 8 free-tier decision), authenticated against Day
5's RBAC, backed by Day 8's RDS instance — the complete architecture,
reachable from any browser, with no server anyone in this course is
personally responsible for keeping running.

This was also, by a wide margin, the most operationally demanding day
of the entire course — today's live session worked through a genuine,
extended debugging chain covering PowerShell argument parsing,
cross-platform Python packaging, CloudFront origin configuration, and
a subtle PowerShell file-copy behavior that silently served stale code
through nearly a dozen "successful" deployments in a row. Every one of
these is documented in detail below, not just because each is a real,
transferable lesson, but because together they reinforce something
Day 8 first raised and today confirmed at a much larger scale:
**deployment introduces an entire category of failure that local
development never has to deal with — a command reporting success while
the actual, observable outcome is quietly wrong, sometimes for
reasons several layers removed from where the symptom appears.**

---

## Deep Dive: AWS Deployment & the App Runner → Lambda Swap

- **Mangum is the entire bridge.** `Mangum(app)` wraps the existing
  FastAPI application, translating between Lambda's event/context
  invocation model and the ASGI interface FastAPI already speaks.
  Every router, dependency, and schema written since Day 4 runs
  completely unmodified — Lambda changed *how the app is hosted*, not
  the app itself.
- **The swap decision, revisited with today's evidence in hand.** Day
  8's research (AWS's July 2025 Free Tier restructuring) predicted
  Lambda would be the more durable choice than App Runner or EC2,
  since its "Always Free" allowance doesn't depend on account age or a
  time-boxed credit balance. Nothing about today's deployment
  experience changes that reasoning — if anything, the packaging
  complexity encountered today is a cost specific to Lambda's
  zip-based deployment model, not a reason to reconsider the
  underlying free-tier decision itself.
- **Deployment as its own discipline.** Today introduced a
  fundamentally different kind of correctness problem than any prior
  day: not "is this code logically right," but "is *this exact
  artifact*, built *this specific way*, actually what's currently
  running." Nearly every real issue today was some version of that
  second question going wrong silently.

---

## Deep Dive: Backend — AWS Lambda

- **Execution role vs. IAM user, a genuinely different identity
  type.** Day 8's `robopulse-admin` is a user — something a person
  authenticates as. Today's `robopulse-lambda-execution-role` is a
  **role** — something Lambda's infrastructure assumes on the
  function's behalf at invocation time, with no password or access
  key of its own. `AWSLambdaBasicExecutionRole` deliberately grants
  only CloudWatch Logs write access — nothing about RDS or S3, since
  the function reaches RDS over a plain database connection and never
  calls AWS's own S3 API directly.
- **Function URLs vs. API Gateway.** A Function URL is a direct,
  built-in HTTPS endpoint on the Lambda function itself — no separate
  API Gateway resource, and no separate service-specific free-tier
  limit to track beyond Lambda's own. Leaving its CORS configuration
  disabled was a deliberate choice: FastAPI's own `CORSMiddleware`
  (since Day 7) is already the complete, tested implementation;
  configuring CORS in two places at once risks them disagreeing.
- **Two separate update operations, two separate purposes.**
  `update-function-code` changes only the deployed code;
  `update-function-configuration` changes only environment
  variables/settings. They're deliberately independent — a pure
  configuration change (like updating `FRONTEND_ORIGIN` in Step 13)
  needs no code repackaging at all, and a pure code change needs no
  configuration touch. **A critical, easy-to-miss detail confirmed
  today:** `update-function-configuration` replaces the *entire*
  `Variables` map in one call — it does not merge or patch individual
  keys. Sending only the one variable being changed silently deletes
  every other one.
- **Cross-platform Python packaging is genuinely fragile, and Docker
  is the more reliable answer.** Lambda runs Linux (Amazon Linux 2023,
  Python 3.12 runtime, glibc 2.34); packages with compiled extensions
  built on Windows will not run there. Asking `pip` to fetch
  Linux-compatible wheels directly from Windows
  (`--platform manylinux_2_28_x86_64 --only-binary=:all:`) is
  documented by pip itself to run in a weaker resolution mode, since
  pip cannot execute any code from a package built for a different
  platform than the one it's running on. Today's live session hit
  every predictable failure mode of that weakness in sequence — a
  version with no matching wheel, the same problem on a transitive
  dependency, a silently *wrong* resolved version, and finally a fully
  unsatisfiable conflict. Building inside `public.ecr.aws/sam/build-python3.12`
  (AWS's own real Amazon Linux 2023 build image, via Docker)
  eliminates the entire category of problem, since packages resolve
  and install on the actual target platform rather than being guessed
  at from a different one — and it costs nothing, since it's a purely
  local build step.
- **`requirements-lambda.txt`, separate from `requirements.txt`.**
  `requirements.txt` (Day 4's `pip freeze` output) pins exact versions
  for everything, including transitive dependencies never imported
  directly. `requirements-lambda.txt` is a minimal, purpose-built list
  for packaging specifically — still pinned (to a confirmed
  mutually-compatible pair, for `pydantic`/`pydantic-core`
  specifically, once ambiguity there caused a resolver conflict), but
  scoped to only what the deployed function actually needs at
  runtime.

---

## Deep Dive: Frontend — React Deployment

- **Vite's build-time environment variables, extended to
  production.** `import.meta.env.VITE_API_BASE_URL` — any variable
  prefixed `VITE_` in a `.env` file — gets baked into the compiled
  JavaScript at `npm run build` time, not read at runtime in the
  browser. `.env.production` specifically is used by `npm run build`
  (as opposed to `npm run dev`), so local development keeps talking to
  `localhost:8000` while a production build talks to the real Lambda
  URL. This is the exact `DATABASE_URL`/`SECRET_KEY`/`FRONTEND_ORIGIN`
  env-var-with-fallback pattern from the backend, now appearing on the
  frontend for the first time — and today's live session confirmed
  directly *why* it matters: a build compiled even slightly before the
  correct `.env.production` value is in place permanently bakes in the
  wrong one, with no way to fix it short of rebuilding.
- **Two S3 buckets, deliberately opposite settings.** Day 8's
  diagnostics bucket stays fully private; today's frontend bucket is
  deliberately public, with Block Public Access disabled and an
  explicit bucket policy granting public `GetObject`. This isn't an
  inconsistency — a static website's entire purpose is being served
  directly to any browser; there's no meaningful sense in which a
  compiled, public-facing React app benefits from being private.
- **`aws s3 sync`, not `aws s3 cp`.** `sync` compares the local
  `dist\` folder against the bucket's current contents, uploading only
  what changed, and `--delete` removes anything in the bucket no
  longer present locally (a prior build's stale files). This is the
  command re-run on every future frontend change, not just today.

---

## Deep Dive: CloudFront

- **Two distinct, easy-to-conflate protocol policies.** **Viewer**
  protocol policy governs the browser-to-CloudFront connection
  (correctly HTTPS, with CloudFront handling the certificate
  automatically). **Origin** protocol policy governs the
  CloudFront-to-S3 connection — and an S3 **static website hosting**
  endpoint supports HTTP *only*, never HTTPS, under any configuration.
  Today's live session hit this directly: leaving origin protocol
  policy on "HTTPS only" (a common default, especially if the console
  auto-detects the domain as an "S3 origin" and offers HTTPS/Origin
  Access Control settings meant for the *different*, REST-style S3
  endpoint) meant CloudFront could never actually connect to the
  origin — surfacing as a 504 Gateway Timeout, with nothing in the
  error pointing back at this specific setting.
- **Caching means "successfully uploaded" and "actually visible" are
  different claims.** CloudFront caches content at edge locations
  independent of what's currently in the origin bucket — a corrected
  build synced to S3 can still serve the *previous* cached version
  until an explicit invalidation
  (`aws cloudfront create-invalidation --paths "/*"`) runs and
  completes. Today's live session needed this twice — once for the
  corrected `VITE_API_BASE_URL` build, and it's worth remembering
  independently of any specific bug: **any** frontend change requires
  this step, not just a fix for a mistake.
- **A third caching layer, easy to forget: the browser itself.**
  Independent of CloudFront's own cache, a browser can hold onto an
  old JS bundle. Testing in an incognito/private window (or a hard
  refresh) rules this layer out specifically, which mattered directly
  during today's live debugging — an invalidation alone wasn't always
  sufficient without also bypassing the browser's own cache.

---

## Deep Dive: CloudWatch

- **Fully automatic, given decisions already made.** Neither Lambda's
  nor CloudFront's logging/metrics required a separate "turn on
  logging" step today — Lambda's came directly from
  `AWSLambdaBasicExecutionRole`'s permissions (Step 2), and
  CloudFront's monitoring is simply a property of being a distinct,
  managed AWS service. Observability wasn't bolted on afterward; it
  was a byproduct of infrastructure decisions already made for other
  reasons.
- **`aws logs tail`, a genuinely load-bearing debugging tool today.**
  Beyond a passive dashboard, `aws logs tail /aws/lambda/robopulse-api
  --since 5m` was the actual tool that, alongside a temporary
  `/debug-cors` diagnostic endpoint, definitively surfaced what the
  running Lambda's configuration truly was — cutting through several
  layers of plausible-but-wrong hypotheses during today's live
  debugging. A response that *looks* wrong doesn't always tell you
  *why*; a log line or a direct diagnostic endpoint, read at the exact
  moment of the failing request, often does.

---

## Architectural Analysis

Today is the fullest expression yet of a pattern this course has
built toward since Day 3: **configuration that lives outside code,
with a local fallback, so the same code runs correctly in more than
one place.** `DATABASE_URL` (Day 3), `SECRET_KEY` (Day 5),
`FRONTEND_ORIGIN` (today, backend) and `VITE_API_BASE_URL` (today,
frontend) are all the same idea, applied consistently across four
different values and both halves of the stack. Step 13's
`FRONTEND_ORIGIN` update — resolving a genuine chicken-and-egg
deployment-ordering problem with zero code changes and no
repackaging — is the clearest possible demonstration of why that
pattern was worth establishing five days before it was strictly
needed.

Today also completes the throughline Day 8 first named explicitly:
**"the command didn't error" is never sufficient confirmation on its
own.** Day 8 demonstrated this once, with a skipped RDS field. Today
demonstrated it at nearly every layer of the deployment pipeline in
turn — a *successful* `pip install` that resolved to the wrong
Pydantic version; a *successful* `aws lambda update-function-code`
that deployed stale code because of `Copy-Item`'s folder-merge
behavior; a *successful* `aws s3 sync` whose result CloudFront simply
hadn't served yet. None of these produced an error at the step where
the actual mistake occurred — every one of them required either an
explicit verification step (checking `pydantic-*.dist-info`'s literal
folder name; grepping the packaged `main.py` for the expected new
code) or a dedicated diagnostic (`/debug-cors`, `aws logs tail`) to
actually surface. This is worth treating as this course's central
deployment-era lesson: **verification has to be deliberate and
specific, not inferred from a clean exit code**, and the more layers a
system has (local file → package → zip → Lambda; local build → S3 →
CloudFront cache → browser cache), the more places a stale or
incorrect artifact can hide at any one of them while every visible
signal says otherwise.

---

## Common Pitfalls & Anti-Patterns

- **The `Copy-Item -Recurse` nesting bug — today's single most
  consequential mistake, and worth understanding precisely.**
  `Copy-Item -Recurse app package\app` behaves differently depending
  on whether `package\app` already exists. The first run, with no
  existing destination, works correctly. Every run after that merges
  the source *into* the existing destination instead of replacing it
  — silently producing a nested `package\app\app\` containing the real
  code, while `package\app\main.py` itself (what actually gets zipped)
  stays frozen at its very first version indefinitely. `-Force` does
  not prevent this — it only permits overwriting individual read-only
  files. This produced a multi-step, genuinely difficult debugging
  session today specifically because every surrounding signal (a
  clean deploy, a byte-verified environment variable, correct-looking
  local source code) pointed away from the actual cause. **Always
  delete the destination folder completely before copying into it
  again — every single time, not just the first.**
- **`curl` in PowerShell silently means `Invoke-WebRequest`, not real
  `curl`.** `-i` gets interpreted as the unrelated `-InFile`
  parameter, producing an error with no obvious connection to the
  actual HTTP request being attempted. Use `curl.exe` explicitly to
  reach the genuine `curl` binary Windows ships by default.
- **AWS CLI environment variable shorthand (`--environment
  "Variables={KEY=value,...}"`), fragile under PowerShell's quoting
  rules.** Values containing special characters (`DATABASE_URL`'s
  colons, slashes, and `@` symbol) are a common way for PowerShell's
  own parsing pass to mangle the string before the AWS CLI ever
  receives it correctly. A JSON file (`--environment
  file://lambda-env.json`) sidesteps shell parsing entirely.
- **Sending only the changed variable to
  `update-function-configuration`.** This call replaces the entire
  `Variables` map — a partial update silently deletes every variable
  not explicitly re-sent.
- **Typing a "random" `SECRET_KEY` by hand.** Hand-typed strings are
  reliably far less random than they appear;
  `secrets.token_hex(32)` generates genuinely high-entropy data.
- **Assuming a corrected upload is immediately visible.** Both
  CloudFront's edge caching and a browser's own local cache can serve
  a stale version well after the underlying source (S3, or the Lambda
  function itself) has been corrected — verification needs an
  explicit invalidation and often an incognito window, not just a
  reload.
- **Confusing origin protocol policy with viewer protocol policy** on
  a CloudFront distribution backed by an S3 static website endpoint —
  the former must be HTTP-only (the endpoint's only supported
  protocol); the latter should be HTTPS (for real browser-facing
  security).

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| `pip install --platform ... -r requirements-lambda.txt` fails to find a version, resolves to an unexpectedly old version, or reports `ResolutionImpossible` | pip's cross-platform install mode is documented to be weaker at dependency resolution, since it can't execute code from packages built for a different platform | Build inside Docker using `public.ecr.aws/sam/build-python3.12` instead — installs natively on the real target platform, no cross-platform guessing |
| `Get-ChildItem package -Filter "pydantic-*"` shows a `1.x` version after packaging | The resolver (especially under pip's cross-platform mode) silently chose an incompatible version | Pin `pydantic`/`pydantic-core` to a confirmed matching pair explicitly, or switch to the Docker-based build |
| `aws lambda update-function-configuration` fails with `ValidationException` about map keys | PowerShell's quoting mangled the inline `--environment "Variables={...}"` shorthand before the AWS CLI parsed it | Use a JSON file (`--environment file://lambda-env.json`) instead |
| After updating `FRONTEND_ORIGIN`, other functionality (database calls, login) breaks | `update-function-configuration` replaces the entire `Variables` map — other variables were omitted and got deleted | Always include every variable in the file, not just the one being changed |
| CloudFront URL returns `504 Gateway Timeout` | Origin protocol policy is set to HTTPS (or "Match viewer"), but an S3 static website endpoint only supports HTTP | Edit the origin: set protocol policy to "HTTP only" |
| Frontend changes (env vars, code) don't appear at the CloudFront URL after rebuilding and re-syncing | CloudFront's edge cache, and/or the browser's own cache, is still serving the previous version | `aws cloudfront create-invalidation --paths "/*"`, wait for "Completed," then test in an incognito window |
| `curl -X OPTIONS ... -i` fails with an error about a missing `-InFile` argument | PowerShell aliases bare `curl` to `Invoke-WebRequest`, a different tool with incompatible flags | Use `curl.exe` explicitly |
| A redeployed Lambda still exhibits old behavior despite a "successful" `update-function-code` | `package\app` wasn't deleted before recopying — `Copy-Item -Recurse` nested the new code one level too deep instead of replacing stale code | `Remove-Item -Recurse -Force package\app` before every `Copy-Item -Recurse`, every time; verify with `Get-Content package\app\main.py \| Select-String "<expected new content>"` before deploying |
| Login fails with `CORS policy: No 'Access-Control-Allow-Origin' header` despite a confirmed-correct `FRONTEND_ORIGIN` | The *deployed* code doesn't actually match the local source — most likely the `Copy-Item` nesting issue above | Confirm what's really deployed with a temporary diagnostic endpoint (e.g. `/debug-cors` returning the live `FRONTEND_ORIGIN` value) rather than continuing to reason about it indirectly |
| A Lambda response shows `400 Bad Request` / `"Disallowed CORS origin"` on an `OPTIONS` request | This is `CORSMiddleware` itself correctly rejecting a preflight whose `Origin` doesn't match `allow_origins` — a real signal, not a false one | Confirm the exact live value with `aws lambda get-function-configuration ... --query "Environment.Variables.FRONTEND_ORIGIN"`, and check for trailing slashes or hidden whitespace via a `repr()`-style inspection if it looks correct but still fails |

---
*RoboPulse Fleet Command Center — Day 9 of 13*
