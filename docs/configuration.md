# Configuration

## Playbook variables

Every role documents its variables in `meta/argument_specs.yml`. 
`ansible-doc -t role <name>` lists them with type, default and description.
Role defaults live in `roles/<name>/defaults/main.yml`.

## User accounts

Defined in `inventories/group_vars/servers/users.yml`:

```yaml
users_accounts:
  - name: <username>
    sudo: true
    ssh_public_key: "<ssh_public_key>"
```

- `sudo: true`: adds the user to the sudo group
- `ssh_public_key`: the user's public SSH key for key-based auth

The security role derives the `AllowUsers` SSH whitelist from this list
automatically, plus the provisioning user (`ansible`) created by the bootstrap
role. Together they are the only accounts allowed to log in. To whitelist
additional pre-existing accounts, extend `security_ssh_extra_allowed_users`.

## Password hashes

Password hashes for sudo users go in `inventories/group_vars/servers/vault.yml`:

```yaml
users_passwords:
  <username>: "<hash>"
```

Only users with `sudo: true` in users.yml need an entry here. Non-sudo users
can skip it.

## Security hardening

Defaults live in `roles/security/defaults/main.yml` and
`roles/packages/defaults/main.yml`.

**Login banner**: shown after login (`/etc/motd`) and before login
(`/etc/issue.net`, via the `Banner` sshd directive):

```yaml
security_banner_text: |
  Authorized access only.
  All activity is monitored and reported.
```

No system-info escape sequences (`\v`, `\m`, `\l`, ...): CIS 1.6.1/1.6.3 forbid them.

**Kernel sysctls**: written by one task in
`roles/security/tasks/system.yml` to `/etc/sysctl.d/99-hardening.conf`:

```yaml
security_sysctls:
  kernel.randomize_va_space: "2"
  fs.suid_dumpable: "0"
  net.ipv4.tcp_syncookies: "1"
  net.ipv4.conf.all.accept_source_route: "0"
  net.ipv4.conf.default.accept_source_route: "0"
  net.ipv4.conf.all.accept_redirects: "0"
  net.ipv4.conf.default.accept_redirects: "0"
  net.ipv4.conf.all.send_redirects: "0"
  net.ipv4.conf.default.send_redirects: "0"
  net.ipv4.conf.all.log_martians: "1"
  net.ipv4.icmp_echo_ignore_broadcasts: "1"
  net.ipv4.conf.all.rp_filter: "1"
  net.ipv4.conf.default.rp_filter: "1"
  net.ipv4.conf.all.secure_redirects: "0"
  net.ipv4.conf.default.secure_redirects: "0"
  net.ipv4.conf.default.log_martians: "1"
  net.ipv6.conf.all.accept_ra: "0"
  net.ipv6.conf.default.accept_ra: "0"
  net.ipv6.conf.all.accept_redirects: "0"
  net.ipv6.conf.default.accept_redirects: "0"
  net.ipv6.conf.all.accept_source_route: "0"
  net.ipv6.conf.default.accept_source_route: "0"
  net.ipv6.conf.all.forwarding: "0"
  net.ipv6.conf.default.forwarding: "0"
```

Covers IPv4 and IPv6 hardening. The only provider-dependent entry is
`net.ipv6.conf.*.accept_ra`: keep it if IPv6 is assigned statically, override
per host if the provider uses SLAAC (see below). IP forwarding is
intentionally *not* set: Docker requires it. Mapped to CIS in
[cis-mapping.md](cis-mapping.md).

**IPv6 `accept_ra` (CIS 3.3.11)**: `0` disables SLAAC auto-configuration. Safe
for static IPv6, breaks SLAAC-based providers. DHCPv6 is not affected by it.
Check before deploying:

```bash
cat /etc/netplan/*.yaml   # explicit IPv6 = static, safe
ip -6 addr show           # how IPv6 is currently assigned
```

If the provider uses SLAAC, override per host by changing just the value to
`"1"`. Note that defining `security_sysctls` in `group_vars`/`host_vars`
replaces the whole role default, so repeat every entry you want to keep:

```yaml
security_sysctls:
  net.ipv6.conf.all.accept_ra: "1"
  net.ipv6.conf.default.accept_ra: "1"
```

**IPv6 forwarding for Docker**: `0` by default, safe for IPv4-only bridge
networks. If you enable IPv6 in Docker (`"ipv6": true` in
`/etc/docker/daemon.json`), override per host:

```yaml
security_sysctls:
  net.ipv6.conf.all.forwarding: "1"
  net.ipv6.conf.default.forwarding: "1"
```

**fail2ban sshd jail**: `jail.local` written by the packages role. Defaults are non-aggressive.

```yaml
packages_fail2ban_bantime: "1h"
packages_fail2ban_findtime: "10m"
packages_fail2ban_maxretry: "5"
```

**SSH TCP forwarding**: disabled by default (CIS 5.1.8). Set to `"yes"`
only if a user needs `ssh -L` / `ssh -R` / `ssh -D` tunnels:

```yaml
security_ssh_allow_tcp_forwarding: "no"
```

**Unattended-upgrades reboot**: automatic reboot after security updates:

```yaml
# Set "true" to enable auto-reboot
security_autoupdate_reboot: "false"

# UTC: avoids the Docker cleanup cron at 03:00
security_autoupdate_reboot_time: "02:00"
```

## Docker cleanup

The weekly cron (`docker system prune -af`, Sundays 03:00) removes stopped
containers, dangling images and build cache. Anonymous volumes are left
untouched by default. Default lives in `roles/docker/defaults/main.yml`:

```yaml
docker_prune_volumes: false
```

Set it to `true` only if all your data lives in named volumes or bind mounts.
With `--volumes` enabled, unused *anonymous* volumes are also deleted.

## Swap

Swap defaults live in `roles/swap/defaults/main.yml`:

```yaml
swap_file_path: /swapfile
swap_file_size_mb: '2048'
swap_swappiness: '60'
```
