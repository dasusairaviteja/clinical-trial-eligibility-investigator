# Level 3 / Project 1 environments

CI runs on dev/main pushes and main pull requests. After tests succeed,
non-PR runs reference ENG, TEST and PROD GitHub environments. GitHub creates
missing environments on first use. These jobs validate configuration only;
the deployment records they create do not mean an Azure app was deployed.

No reviewers or secrets are configured by this workflow. Routine runs require
no manual approval unless repository administrators add protection rules.
Existing protections must never be bypassed. Before cloud deployment is added,
restrict production deployment to main and use environment-scoped identity.
Local .env files are ignored; hosted runners cannot read a developer's local file.
Keep .env.example placeholders only. This increment does not load dotenv files.

Python 3.12 standard library only; no external Python packages are selected.
Action revisions are pinned to verified stable releases (checkout 4.2.2,
setup-python 5.6.0), avoiding a runtime-major migration for this initial setup.
Official references checked during implementation:
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- https://docs.python.org/3/library/unittest.html
- https://docs.python.org/3/library/enum.html

Next: real deployment requires a built application, Azure targets, identity and
budget configuration; none are provisioned by this change.
