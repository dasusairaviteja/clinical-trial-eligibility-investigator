# Packaging and Azure preparation

The container serves the authenticated WSGI workspace on port 8000. Build with
`docker build -t triallens:local .`. Use a read-only root filesystem, a temporary
/tmp mount and a durable **local block-backed** /data mount owned by UID/GID 10001.
Do not use SQLite on a shared network filesystem or multiple replicas. Provide
REVIEWER_TOKENS_JSON through a private runtime environment/secret manager; never
bake it into an image. Copy only approved synthetic registry snapshots.

CI builds the image and starts it as UID 10001 with dropped capabilities and
no-new-privileges. Its /data mount is temporary for the test; production needs
durable storage, encrypted backup and a tested restore procedure.

## ENG, TEST, PROD

`infra/main.bicep` defines private Azure VM infrastructure with SSH key-only login,
Trusted Launch, managed identity and a retained managed OS disk. Separate resource
groups/names are declared in infra/environments.json. The template references an
existing subnet and has no public IP or public application endpoint.

Prepare a private ARM parameters file with environment, subnetId, managementCidr,
sshPublicKey and a region-available pinned Canonical Ubuntu 24.04 imageVersion.
Optional parameters are location and vmSize. SSH public keys are not credentials,
but private keys and application tokens must never appear in the parameter file.
Do not put private deployment files in this repository.

After an operator authenticates Azure and confirms the intended subscription:

```sh
python scripts/azure_deploy.py ENG /private/path/eng.parameters.json
```

This defaults to Azure what-if. Actual provisioning requires both `--apply` and
`--budget-approved`; only use those after budget authorization. No such command
has been run by this project delivery. Resource-group creation is intentionally
separate and requires authorized administration. Repeat independently for TEST
and PROD with their own parameters; mismatched environment settings are rejected.

After infrastructure deployment, install a supported container engine on the VM,
place secrets under operator-managed permissions, bind the application to loopback,
and configure an approved TLS/authentication ingress. These host configuration and
cloud validation tasks are still pending. Do not open port 8000 publicly. Promote
the same verified image digest ENG → TEST → PROD only after environment acceptance.
For rollback, retain the last verified image digest, stop writes, take a verified
backup, and restore into a new database file before switching the service. Retained
Azure disks still incur charges; deletion needs separate operator authorization.

Official references consulted:
- https://docs.docker.com/build/building/best-practices/
- https://learn.microsoft.com/en-us/azure/templates/microsoft.compute/virtualmachines
- https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/bicep-cli
- https://playwright.dev/docs/ci (Playwright package: Apache-2.0)
- https://hl7.org/fhir/R4/observation.html (schema reference; no real FHIR dataset copied)
