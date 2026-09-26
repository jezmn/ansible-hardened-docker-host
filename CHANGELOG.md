# Changelog

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
