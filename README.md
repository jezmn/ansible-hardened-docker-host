# Ansible Hardened Docker Host

Ansible playbooks that turn a fresh Ubuntu server into a hardened
Docker host: SSH locked down, UFW firewall, sudo user accounts, 
and Docker ready to run containers.

**Supported platform:** Ubuntu 24.04 LTS is the primary target: the CIS
mapping ([docs/cis-mapping.md](docs/cis-mapping.md)) and the Molecule scenario
run against 24.04. 22.04 is compatible (all sshd options and packages used are
available there) but is not CI-verified.

## Features

### Security

- Key-only SSH: password auth off, root restricted to key login, and an
  `AllowUsers` whitelist derived automatically from your user list plus the
  provisioning user.
- Brute-force protection: `MaxAuthTries 3`, `LoginGraceTime 30`, idle timeout,
  plus a fail2ban sshd jail (configurable bantime/findtime/maxretry,
  config validated before use).
- UFW deny-incoming with 22/80/443, kernel sysctls (ASLR, SYN cookies, source
  routing/redirects blocked, martian logging), auditd, and a legal login
  banner on motd + issue.net.
- Unattended-upgrades enabled with a configurable auto-reboot window.

### Docker host

- Docker CE + buildx + compose plugin from the official repo, weekly
  `docker system prune` (volume pruning opt-in).
- Removes Ubuntu's stale `docker.io`/`containerd` first, so the official repo
  never conflicts with the distro packages.
- Repository uses the host's release codename.

### Reliability

- Neutralizes the cloud-init SSH override that otherwise keeps password
  auth enabled.
- Backs up sshd config and ships a rollback playbook, verified by a Molecule
  damage test.
- sshd, fail2ban and sudoers configs are validated before the service
  restarts.

### Template-ready

- Secrets via Ansible Vault; users managed from one `users_accounts` list.
- Every variable documented via argument specs (`ansible-doc -t role <name>`),
  a CIS benchmark mapping, and a decisions log explaining *why* each choice.
- Fully-qualified collection names (FQCN) throughout, enforced by ansible-lint
  in CI.

## Quick start

Full walkthrough: [Getting started](docs/getting-started.md).

```bash
# Install deps
ansible-galaxy collection install -r requirements.yml

# Build and install the collection locally
ansible-galaxy collection build
ansible-galaxy collection install jezmn-ansible_hardened_docker_host-*.tar.gz

# Bootstrap: creates `ansible` provisioning user
# Set `ansible` user's key first
# Drop -k if your provider login uses an SSH key instead of a password
cp inventories/hosts-bootstrap.ini.example inventories/hosts-bootstrap.ini
ansible-playbook -i inventories/hosts-bootstrap.ini playbooks/bootstrap.yml -k

# Main playbook: set users/vault vars first
cp inventories/hosts.ini.example inventories/hosts.ini
ansible-playbook -i inventories/hosts.ini playbooks/site.yml --ask-vault-pass
```

## What it does

| Role | What |
|---|---|
| `bootstrap` | (separate playbook) Create the ansible provisioning user |
| `wait_for_connection` | Wait for SSH to come up, then gather facts |
| `packages` | apt upgrade, base tools, UTC timezone, UDP tuning, fail2ban sshd jail, remove Snap |
| `docker` | Docker CE + buildx + compose from official repo, weekly cleanup cron |
| `firewall` | UFW: deny incoming, allow 22/80/443 |
| `users` | Sudo accounts with SSH keys + password hashes |
| `security` | SSH hardening, kernel sysctls (CIS 3.3.x), auditd, cloud-init override fix, unattended upgrades |
| `swap` | Swap file (adapted from geerlingguy) |
| `reboot_if_needed` | Reboot on pending kernel update |

> Note: kernel-level tasks are skipped inside containers. See [Testing with Molecule](#testing-with-molecule).

## Repository layout

```
.
├── playbooks/
│   ├── site.yml
│   ├── bootstrap.yml
│   └── rollback-ssh.yml
├── inventories/
│   ├── hosts.ini.example
│   ├── hosts-bootstrap.ini.example
│   └── group_vars/
│       ├── bootstrap.yml
│       └── servers/
│           ├── users.yml
│           └── vault.yml
├── molecule/
│   ├── bootstrap/
│   ├── default/
│   └── rollback/
├── roles/
│   ├── bootstrap/
│   ├── docker/
│   ├── firewall/
│   ├── packages/
│   ├── reboot_if_needed/
│   ├── security/
│   ├── swap/
│   ├── users/
│   └── wait_for_connection/
├── docs/
│   ├── getting-started.md
│   ├── configuration.md
│   ├── cis-mapping.md
│   └── decisions.md
├── .github/
│   └── workflows/
│       ├── ansible-lint.yml
│       └── molecule-test.yml
├── .ansible-lint
├── .gitignore
├── LICENSE
├── README.md
├── galaxy.yml
├── meta/
│   └── runtime.yml
├── requirements-dev.txt
└── requirements.yml
```

## Documentation

| File | What |
|---|---|
| [Getting started](docs/getting-started.md) | Full setup guide |
| [Configuration](docs/configuration.md) | Variables, users, vault, security, docker cleanup, swap |
| [CIS mapping](docs/cis-mapping.md) | Security controls mapped to CIS |
| [Decisions](docs/decisions.md) | Why the code looks the way it does |

## Testing with Molecule

Requires Docker. Create a virtualenv and install the dev dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run a single scenario, or all of them:

```bash
molecule test -s default
molecule test -s bootstrap
molecule test -s rollback
molecule test --all    # all scenarios
```

The default scenario runs the full pipeline (packages, users, security,
docker) inside a Docker container (`geerlingguy/docker-ubuntu2404-ansible`),
and the `bootstrap` scenario separately verifies that the `ansible`
provisioning user (account, SSH key, passwordless sudo) is created from root.

The container shares the host kernel, so tasks that touch the kernel or
system services that cannot start in a container are skipped when
`ansible_facts.virtualization_type` reports `docker`/`container`:

- `packages`: UDP receive/send buffer sysctls (`net.core.rmem_max`,
  `net.core.wmem_max`)
- `packages`: UTC timezone (shares clock/kernel with the host)
- `security`: kernel hardening sysctls and auditd service enablement

Those controls are applied and validated on a real server (physical or
virtual), not inside the Molecule container.

The `firewall` and `swap` roles are intentionally excluded from Molecule:
UFW cannot meaningfully manage the host firewall from inside a container, and
`swapon` is denied by cgroup v2 in non-root containers. Both are validated on a
real server instead.

A dedicated `rollback` scenario verifies the SSH rollback path:
`side_effect damage.yml` breaks the sshd config, then `rollback-ssh.yml`
(playbooks/) restores it from the `.ansible-backup`. The verify step runs
immediately after the rollback (no re-converge in between), asserting the
restored file matches the backup byte-for-byte, keeps mode `0600` (CIS 5.1.1),
and still parses with `sshd -T`.

## Acknowledgments

Based on [guillaumebriday/kamal-ansible-manager](https://github.com/guillaumebriday/kamal-ansible-manager),
modified and extended for this setup.

The `swap` role is adapted from
[geerlingguy/ansible-role-swap](https://github.com/geerlingguy/ansible-role-swap).

Modifications and rationale for both are documented in
[docs/decisions.md](docs/decisions.md).

## License

MIT
