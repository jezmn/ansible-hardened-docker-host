# Changelog

## 0.3.0

- Cap journald disk usage with `SystemMaxUse=1G`.
- Seed `/etc/docker/daemon.json` with log rotation (`max-size`, `max-file`)
  and builder garbage collection on first run.
- Replace the aggressive weekly prune with a selective cleanup: images older
  than 168h, plus `docker builder prune --keep-storage=5GB`.
- Document the new docker and security role variables in `argument_specs`.

## 0.2.2

- Install sudo before configuring bootstrap sudoers.
- Fix Galaxy setup instructions and documentation links.

## 0.2.1

- Fix the users role failing when an account has `sudo: false`.

## 0.2.0

- Debian 13 support: the Docker role now resolves the apt repository and GPG
  key from the target distribution, and asserts the host is Ubuntu or Debian.
- Fix the swap role on hosts where hardware facts are missing.
- Fix fail2ban config validation in check mode.
- Docs: `--check --diff` preview command, and a note that removing an account
  from `users_accounts` blocks new SSH logins.

## 0.1.2

- Quick start is now pure Galaxy.
- Inventory is documented as user-owned.
- Absolute links in role READMEs so they resolve on Galaxy. 

## 0.1.1

- Add per-role READMEs and role metadata required by Galaxy import.

## 0.1.0

- Provision a hardened Docker host from a fresh Ubuntu server.
- Initial packaging as the `jezmn.ansible_hardened_docker_host` collection.
