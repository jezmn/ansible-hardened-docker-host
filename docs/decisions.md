# Decisions log

Record of design decisions and their rationale.

## No MFA (TOTP)

SSH is key-only by design and optimized for automation. MFA via PAM requires
`keyboard-interactive`, which breaks Ansible, rsync and git-over-SSH unless
the automation account is exempted. Every new user would also have to enroll
a TOTP token by hand. So the trade-off is key-only auth + fail2ban +
`AllowUsers` whitelist, no MFA.

## AllowUsers derived from `users_accounts`

The security role writes `AllowUsers` from the user list in
`inventories/group_vars/servers/users.yml` instead of a separate variable. A manually
maintained list would be a foot-gun: adding a user to `users_accounts` and
forgetting to add them to the SSH whitelist would lock them out.

**Exception: The provisioning user.** The `ansible` account is created by the
bootstrap role, not by `users`, so listing it in `users_accounts` would
duplicate its management (user creation, password hash). It is whitelisted
via `security_ssh_extra_allowed_users`, whose default is `[ansible]`.

## Docker cleanup cron without `--volumes` by default

Weekly `docker system prune -af` on Sundays at 03:00. `--volumes` is off by
default (`docker_prune_volumes: false`) because pruning unused *anonymous*
volumes can delete data that only lives in a volume (e.g. a database). Safe
default; opt in via the variable if all data lives in named volumes or bind
mounts.

## Docker GPG key with `force: true`

The key is fetched with `force: true` (~2KB per run). Without it, `get_url`
only replaces the local key when the remote `Last-Modified` header is newer.
A key rotation that keeps the old timestamp leaves the server on the old key,
and `apt update` fails signature validation.

## No user added to the `docker` group

The docker role does not add any user to the `docker` group. Membership is
equivalent to passwordless root on the host (a container can mount the
whole filesystem), and the `users` role already grants sudo. Operators run
`sudo docker` instead. Keeping the group empty preserves a sudo boundary
and avoids a second, easily forgotten privilege grant.

## SSH hardening

The settings and their CIS mapping are in `docs/cis-mapping.md` (5.1.x).
Every change is validated with `sshd -T -f %s` before the service restarts.

TCP forwarding is disabled by default (`security_ssh_allow_tcp_forwarding`,
CIS 5.1.8). It is a variable: a setup that relies on `ssh -L/-R/-D` tunnels
can set it to `"yes"`.

Agent forwarding (`AllowAgentForwarding no`) is disabled unconditionally in
the sshd loop: rarely needed and a bigger pivot risk, so no opt-out.

## Unattended-upgrades explicitly enabled

Installing the `unattended-upgrades` package is not enough: the actual
automatic run is gated by `/etc/apt/apt.conf.d/20auto-upgrades` with
`APT::Periodic::Update-Package-Lists "1"` and
`APT::Periodic::Unattended-Upgrade "1"`. Stock Ubuntu images ship both
enabled, but minimal images may not, so the security role ensures both
explicitly (CIS 1.2.2.1). Otherwise the playbook would claim compliance while
doing nothing.

## Reboot time 02:00 to avoid the Docker cleanup cron

Unattended-upgrades auto-reboot is set to 02:00 UTC. The Docker cleanup cron
runs at 03:00 Sunday. Two reboot/cleanup jobs at the same hour would race.

## cloud-init SSH override fix

Newer Ubuntu releases ship `/etc/ssh/sshd_config.d/50-cloud-init.conf`, which
sets `PasswordAuthentication yes`. Because sshd reads it before
`/etc/ssh/sshd_config` (the `Include` is at the top of the file) and OpenSSH
uses first-match-wins, it overrides a `PasswordAuthentication no` set in the
main file, keeping password auth enabled. The security role neutralizes it
(and backs it up first) when present. Without this, `PasswordAuthentication
no` alone never takes effect.

## Swap role adapted from geerlingguy

The `swap` role is adapted from
[geerlingguy/ansible-role-swap](https://github.com/geerlingguy/ansible-role-swap).
No external dependency to set up, and the files are tracked in the repo.

Modified on top of the original:

- `swap_file_size_mb` defaults to `2048` (upstream: `512`).
- The create command is chosen per filesystem: `fallocate` on ext2/3/4,
  `dd` otherwise. Instant on the default ext4, and avoids hole-filled files
  that `swapon` rejects on btrfs/xfs.
- `mkswap`/`swapon` run as handlers (only when the file changes) instead of
  inline tasks.

## Once-only config backups + rollback playbook

The security role backs up `sshd_config` and the cloud-init override to
`.ansible-backup` once, before modification (stat + `when` guard), so the
original config is preserved for rollback.

`playbooks/rollback-ssh.yml` restores the backups. The Molecule `default`
scenario damages the SSH config and verifies the rollback recovers it.

## fail2ban sshd jail

fail2ban is installed by the packages role and configured with a real
`jail.local`. Defaults: `bantime 1h`, `findtime 10m`, `maxretry 5`, systemd
journal backend. 

Values are variables (`packages_fail2ban_bantime`, ...), kept
non-aggressive deliberately, since a permanent ban (`-1`) risks locking
yourself out.
Config is validated with `fail2ban-client -t` as a separate task, not a
template `validate:`: the module appends the file path as an argument that
`fail2ban-client` does not accept.

## Kernel sysctls via `security_sysctls` dict

CIS 3.3.x network hardening is written in `roles/security/tasks/system.yml` by
an `ansible.posix.sysctl` task that loops over the `security_sysctls` dict to
`/etc/sysctl.d/99-hardening.conf`; the same file also pins `rp_filter` per
interface.

Covers IPv4 and IPv6. The IPv6 entries were added after the live audit flagged
CIS 3.3.11 (`accept_ra`) plus the IPv6 forwarding and source-route checks.
`accept_ra` is the only provider-dependent one: disabling it blocks SLAAC
auto-configuration, which is safe on providers that assign IPv6 statically but
breaks IPv6 on SLAAC-based ones. How to check and override per host is in
cis-mapping.md, "Provider-dependent decisions". IP forwarding
(`net.ipv4.ip_forward`) is *not* set: Docker needs it enabled, so the CIS
control is intentionally not enforced (noted in cis-mapping.md).

## auditd installed, rules intentionally not configured

CIS 6.2.1.1 / 6.2.1.2 require the audit daemon installed and enabled. The role installs
`auditd` + `audispd-plugins` and enables the service only when
`ansible_virtualization_type not in ["docker", "container"]`: auditd cannot
start in an unprivileged container.

CIS 6.2.3.x audit rules (`-w` watches, immutable `-e 2`) are deliberately out
of scope: per-system audit needs are site-specific, and a bad rule set is
worse than none.

## chrony instead of systemd-timesyncd

Ubuntu 24.04 ships `systemd-timesyncd` installed but inactive. The playbook
installs `chrony` instead for multi-source sync with drift correction.

## ufw instead of nftables

The SSG 24.04 profile covers CIS 4.2.x with raw `nft` rules. This repo uses
`ufw` (`community.general.ufw`) instead: a declarative front-end over the same
iptables chains with less room for aliasing mistakes and keeps Molecule CI
stable. nftables stays an option if per-interface or dynamic rulesets are ever
needed.
