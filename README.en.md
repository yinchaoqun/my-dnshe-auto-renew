# DNSHE Auto Renew

[中文](./README.md) | [English](./README.en.md)

One-line summary: this package checks your DNSHE domains once a week and renews them automatically after they enter the renewal window.

## 3-Minute Setup

### Step 0: create your DNSHE API credentials first

Go here first:

- https://my.dnshe.com

Prepare these two values:

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

### Step 1: turn this repository into your own private repository

**Use Route A: GitHub Importer as the recommended method.** It avoids manually moving files.

| Route | Recommendation | Best for |
| --- | --- | --- |
| **Route A: import with GitHub Importer** | **Recommended** | Everyone. Everything happens in the browser |
| Route B: download ZIP + copy and paste | Backup only | Everyone. |

> **Choose only one route.** Use Route A by default; consider Route B only if you explicitly want to copy files manually.

#### Route A: import with GitHub Importer (recommended)

**A-1. Open GitHub Importer**

1. Log in to GitHub.
2. Open: <https://github.com/new/import>

**A-2. Fill in the import form**

| Field | Value |
| --- | --- |
| `Your old repository's clone URL` | `https://github.com/OUBIGFA/dnshe-auto-renew` |
| `Owner` | Your GitHub account |
| `Repository name` | Your repository name, for example `my-dnshe-auto-renew` |
| `Privacy` | Select `Private` |

Then click `Begin import`. It usually finishes in a few seconds to a few minutes.

**A-3. Open your imported private repository**

After the import finishes, GitHub will create a private repository under your own account. The secrets, variable, and workflow in the next steps can all be configured directly on that repository's GitHub page.

Continue to "Step 2".

<details>
<summary><b>Route B: download ZIP + copy and paste (backup manual method) - click to expand</b></summary>

<br>

If you do not want to use GitHub Importer, you can do it manually: create a new `Private` repository on GitHub, then open the original project <https://github.com/OUBIGFA/dnshe-auto-renew>, click `Code` -> `Download ZIP`, extract the source code, and copy the files into your own private repository.

</details>

Why use a private repository:

- `DNSHE_DOMAINS` shows which domains you manage
- `state/domains-state.json` stores known expiration times
- those are operational details and are better kept private

### Step 2: add 2 secrets and 1 variable in GitHub

Go to:

- `Settings -> Secrets and variables -> Actions`

Add these secrets:

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

Add this variable:

- `DNSHE_DOMAINS`

### Step 3: write your domains into `DNSHE_DOMAINS`

Use one domain per line:

```text
abc88.cc.cd
12366.cc.cd
```

### Step 4: run the workflow once manually

Open:

- `Actions`

Run `DNSHE Auto Renew` once and confirm:

- the domains are read correctly
- `state/domains-state.json` is created correctly

## You only need to fill in 3 things

1. `DNSHE_API_KEY`
2. `DNSHE_API_SECRET`
3. `DNSHE_DOMAINS`

Everything else can usually stay unchanged.

## How to write `DNSHE_DOMAINS`

Just use one domain per line:

```text
abc88.cc.cd
12366.cc.cd
444.cc.cd
```

Later:

- add a domain: add one line
- remove a domain: delete one line

## What happens when you add a new domain later

Assume you currently have:

```text
abc88.cc.cd
12366.cc.cd
```

Thirty days later, you add:

```text
444.cc.cd
```

You only need to update `DNSHE_DOMAINS` to:

```text
abc88.cc.cd
12366.cc.cd
444.cc.cd
```

On the next workflow run, it will automatically:

1. detect that `444.cc.cd` is new
2. read its `created_at` from the DNSHE API
3. calculate the first expiration as `created_at + 365 days`
4. save the result into `state/domains-state.json`

So you do not need to manually fill in either the registration time or the expiration time.

## Why you do not need to enter expiration dates manually

This workflow calculates them automatically:

- first time seen: `created_at + 365 days`
- after a successful renewal: use the API field `new_expires_at`

That means the next renewal window keeps updating automatically.

## When renewal happens

Default behavior:

- renewal becomes allowed `175 days` before expiration
- the workflow checks once per week
- once a domain enters the window, it renews automatically

## If you regenerate the DNSHE API credentials

Just update these GitHub Secrets:

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

## Local Dry Run

```powershell
$env:DNSHE_API_KEY='your_key'
$env:DNSHE_API_SECRET='your_secret'
$env:DNSHE_DOMAINS="abc88.cc.cd`n12366.cc.cd`n444.cc.cd"
python .\scripts\dnshe_auto_renew.py --state .\state\domains-state.json --dry-run
```

`--dry-run` only checks the logic. It does not renew anything and does not change the state file.

## Change the schedule

Edit the `cron` value in:

- `.github/workflows/dnshe-auto-renew.yml`

The schedule uses UTC.

## Files

- `scripts/dnshe_auto_renew.py`
- `.github/workflows/dnshe-auto-renew.yml`
- `state/domains-state.json`

## Official Docs

- [DNSHE dashboard](https://my.dnshe.com)
- [DNSHE API manual](https://my.dnshe.com/knowledgebase/1/Free-Domain-Name-Service-API-User-Manual.html)
