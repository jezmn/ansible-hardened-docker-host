# CIS Benchmark Mapping: Ubuntu 24.04 LTS

Security controls in this playbook, mapped to the
[CIS Ubuntu Linux 24.04 LTS Benchmark v1.0.0](https://www.cisecurity.org/benchmark/ubuntu_linux).
Control IDs were verified against the live audit run with the community
ComplianceAsCode / SCAP Security Guide content
([v0.1.81](https://github.com/ComplianceAsCode/content/releases/tag/v0.1.81),
`ssg-ubuntu2404-ds.xml`, profile `cis_level1_server`). Compliance is partial,
with documented deviations and pending items.

> Scope: the mapping and the live OpenSCAP audit below were verified on
> **Ubuntu 24.04 LTS**. It should also work on 22.04 since everything this
> playbook uses is available on both, but a 22.04 compliance claim needs its
> own benchmark run.

> The security role is split into focused task files (`roles/security/tasks/`):
> `ssh.yml`, `ssh_cloud_init.yml`, `sshd_config.yml`, `system.yml`, `logging.yml`,
> `access.yml`, `updates.yml` (dispatched in order from `main.yml`). File
> references below point to the individual files.

| CIS Control | Description | Covered by |
|---|---|---|
| 1.1.1.1-1.1.1.5, 1.1.1.9 | Ensure filesystem and storage kernel modules are not available | `roles/security/tasks/system.yml`: `/etc/modprobe.d/99-hardening.conf` sets `install cramfs\|freevxfs\|hfs\|hfsplus\|jffs2\|usb-storage /bin/true` (stricter than `blacklist`). Deviation: SSG's `kernel_module_*` checks expect a literal `blacklist` line, so the audit flags them despite the stricter protection; 1.1.1.6 overlayfs not blocked (Docker requires it); 1.1.1.7 squashfs and 1.1.1.8 udf left as-is |
| 1.1.2.1.1 | Ensure /tmp is configured on its own partition | Not implemented: `/tmp` is on the root filesystem; no dedicated partition (pending decision, rule `partition_for_tmp` flagged) |
| 1.2.1.1 | Ensure GPG keys are configured | `roles/docker/tasks/main.yml`: Docker GPG key |
| 1.2.1.2 | Ensure package manager repositories are configured | `roles/docker/tasks/main.yml`: Docker repository only, other sources left as shipped |
| 1.2.2.1 | Ensure updates, patches, and additional security software are installed | `roles/packages/tasks/main.yml`: `apt upgrade` |
| 1.3.1.1-1.3.1.3 | Ensure AppArmor is installed, enabled and profiles are enforcing | Not enforced: AppArmor kernel support is active (Ubuntu default) but `apparmor-utils` is not installed and profiles are left as shipped; `grub2_enable_apparmor` fails because the boot entry has no explicit `apparmor=1 security=apparmor` flags |
| 1.4.1 | Ensure bootloader password is set | Not implemented: no console/BIOS access on the provider; a GRUB password would lock out rescue mode (rules `grub2_password`, `grub2_uefi_password` flagged) |
| 1.5.1 | Ensure address space layout randomization is enabled | `roles/security/tasks/system.yml`: `kernel.randomize_va_space=2` |
| 1.5.3 | Ensure core dumps are restricted | `roles/security/tasks/system.yml`: `fs.suid_dumpable=0` sysctl + `* hard core 0` in `/etc/security/limits.d/99-disable-core.conf` |
| 1.5.5 | Ensure Automatic Error Reporting is not enabled | `roles/security/tasks/system.yml`: stops/disables `apport` service and sets `enabled=0` in `/etc/default/apport`. Deviation: the `service_apport_disabled` check wants `systemctl mask`; we use stop+disable+`enabled=0` (same practical effect), so the audit flags it |
| 1.6.1 | Ensure message of the day is configured properly | `roles/security/tasks/ssh.yml`: `/etc/motd` banner |
| 1.6.3 | Ensure remote login warning banner is configured properly | `roles/security/tasks/ssh.yml`: `/etc/issue.net` banner |
| 2.1 (family) | Ensure non-essential services are not in use | Not explicitly enforced: only snap is removed |
| 2.1.20 | Ensure X window server services are not in use | Not explicitly enforced: not present on the stock server image |
| 2.3.3.1 | Ensure chrony is configured with an authorized timeserver | `roles/packages/tasks/main.yml` installs chrony (stock config) |
| 2.3.3.2 | Ensure chrony is running as user `_chrony` | Default chrony config: covered |
| 2.4.1.1 | Ensure cron daemon is enabled and active | `roles/docker/tasks/main.yml`: installs cron + scheduled cleanup |
| 2.4.1.2-2.4.1.7 | Ensure permissions on cron configuration are configured | `roles/security/tasks/access.yml`: `/etc/crontab` `0600`; `/etc/cron.d`, `/etc/cron.{hourly,daily,weekly,monthly}` `0700` |
| 2.4.1.8 | Ensure crontab is restricted to authorized users | `roles/security/tasks/access.yml`: `/etc/cron.allow` `0640` root:crontab, contains `root` + `users_accounts` |
| 2.4.2.1 | Ensure at is restricted to authorized users | `roles/security/tasks/access.yml`: `/etc/at.allow` `0640` root:root, same content as `cron.allow` |
| 3.3.1 | Ensure IP forwarding is disabled | Intentionally not enforced: Docker requires IP forwarding |
| 3.3.2 | Ensure packet redirect sending is disabled | `roles/security/tasks/system.yml`: `net.ipv4.conf.*.send_redirects=0` |
| 3.3.4 | Ensure broadcast ICMP requests are ignored | `roles/security/tasks/system.yml`: `net.ipv4.icmp_echo_ignore_broadcasts=1` |
| 3.3.5 | Ensure ICMP redirects are not accepted | `roles/security/tasks/system.yml`: `net.ipv4.conf.*.accept_redirects=0` |
| 3.3.6 | Ensure secure ICMP redirects are not accepted | `roles/security/tasks/system.yml`: `net.ipv4.conf.*.secure_redirects=0` |
| 3.3.7 | Ensure reverse path filtering is enabled | `roles/security/tasks/system.yml`: `net.ipv4.conf.*.rp_filter=1` on `all`, `default` and every live interface; conflicting `rp_filter=2` lines in the image's `10-network-security.conf` are commented out. Audit: pass |
| 3.3.8 | Ensure source routed packets are not accepted | `roles/security/tasks/system.yml`: `net.ipv4.conf.*.accept_source_route=0`; IPv6 variant also pinned (`net.ipv6.conf.*.accept_source_route=0`) |
| 3.3.9 | Ensure suspicious packets are logged | `roles/security/tasks/system.yml`: `net.ipv4.conf.all.log_martians=1` and `net.ipv4.conf.default.log_martians=1`; conflicting `log_martians` lines in `/etc/ufw/sysctl.conf` are commented out. Audit: pass |
| 3.3.10 | Ensure TCP SYN cookies is enabled | `roles/security/tasks/system.yml`: `net.ipv4.tcp_syncookies=1` |
| 3.3.11 | Ensure IPv6 router advertisements are not accepted | `roles/security/tasks/system.yml`: `net.ipv6.conf.*.accept_ra=0`; IPv6 `accept_redirects` and `forwarding` also pinned |
| 4.1.1 | Ensure a single firewall configuration utility is in use | `roles/firewall/tasks/main.yml`: only ufw is configured; nftables/iptables-persistent not set up |
| 4.2.1 | Ensure ufw is installed | `roles/packages/tasks/main.yml` installs ufw |
| 4.2.2 | Ensure iptables-persistent is not installed with ufw | Not explicitly enforced: not installed on the stock image |
| 4.2.3 | Ensure ufw service is enabled | `roles/firewall/tasks/main.yml`: `state: enabled` |
| 4.2.4 | Ensure ufw loopback traffic is configured | Default ufw behavior: not explicitly configured |
| 4.2.5 | Ensure ufw outbound connections are configured | `roles/firewall/tasks/main.yml`: `policy: allow` outgoing |
| 4.2.6 | Ensure ufw firewall rules exist for all open ports | `roles/firewall/tasks/main.yml`: SSH (22), HTTP (80), HTTPS (443) |
| 4.2.7 | Ensure ufw default deny firewall policy | `roles/firewall/tasks/main.yml`: `policy: deny` incoming |
| 5.1.1 | Ensure permissions on /etc/ssh/sshd_config are configured | `roles/security/tasks/sshd_config.yml`: `mode: "0600"` on sshd_config, its `.ansible-backup` copies and the `50-cloud-init.conf` drop-in (+ its backup, enforced even when the backup already exists) |
| 5.1.4 | Ensure sshd access is configured | `roles/security/tasks/sshd_config.yml`: `AllowUsers` derived from `users_accounts` |
| 5.1.5 | Ensure sshd Banner is configured | `roles/security/tasks/sshd_config.yml`: `Banner /etc/issue.net` |
| 5.1.6 | Ensure sshd Ciphers are configured | `roles/security/tasks/sshd_config.yml`: explicit Ciphers list (CIS-approved set) |
| 5.1.7 | Ensure sshd ClientAliveInterval and ClientAliveCountMax are configured | `roles/security/tasks/sshd_config.yml`: `ClientAliveInterval 300`, `ClientAliveCountMax 2`. Deviation: CIS asks for 3, we keep 2 (stricter); the audit flags the value mismatch, not a real gap (rules `sshd_set_idle_timeout`, `sshd_set_keepalive`) |
| 5.1.8 | Ensure sshd DisableForwarding is enabled | `roles/security/tasks/sshd_config.yml`: `X11Forwarding no` + `AllowAgentForwarding no` + `AllowTcpForwarding no` (via `security_ssh_allow_tcp_forwarding`) |
| 5.1.9 | Ensure sshd GSSAPIAuthentication is disabled | `roles/security/tasks/sshd_config.yml`: `GSSAPIAuthentication no` |
| 5.1.10 | Ensure sshd HostbasedAuthentication is disabled | `roles/security/tasks/sshd_config.yml`: `HostbasedAuthentication no` |
| 5.1.11 | Ensure sshd IgnoreRhosts is enabled | `roles/security/tasks/sshd_config.yml`: `IgnoreRhosts yes` |
| 5.1.12 | Ensure sshd KexAlgorithms is configured | `roles/security/tasks/sshd_config.yml`: explicit KexAlgorithms list (CIS-approved set) |
| 5.1.13 | Ensure sshd LoginGraceTime is configured | `roles/security/tasks/sshd_config.yml`: `LoginGraceTime 30` |
| 5.1.14 | Ensure sshd LogLevel is configured | `roles/security/tasks/sshd_config.yml`: `LogLevel INFO` |
| 5.1.15 | Ensure sshd MACs are configured | `roles/security/tasks/sshd_config.yml`: explicit MACs list matching SSG's strong set exactly (`hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,hmac-sha2-512,hmac-sha2-256`); weak `hmac-sha1`/`umac-64*`/`umac-128*` excluded. Audit: pass |
| 5.1.16 | Ensure sshd MaxAuthTries is configured | `roles/security/tasks/sshd_config.yml`: `MaxAuthTries 3` |
| 5.1.17 | Ensure sshd MaxSessions is configured | `roles/security/tasks/sshd_config.yml`: `MaxSessions 10` |
| 5.1.18 | Ensure sshd MaxStartups is configured | `roles/security/tasks/sshd_config.yml`: `MaxStartups 10:30:60` |
| 5.1.19 | Ensure sshd PermitEmptyPasswords is disabled | `roles/security/tasks/sshd_config.yml`: `PermitEmptyPasswords no` |
| 5.1.20 | Ensure sshd PermitRootLogin is disabled | Deviation: `PermitRootLogin prohibit-password` (bootstrap logs in as root) |
| 5.1.21 | Ensure sshd PermitUserEnvironment is disabled | `roles/security/tasks/sshd_config.yml`: `PermitUserEnvironment no` |
| 5.2.1 | Ensure sudo is installed | Installed by default on Ubuntu 24.04 |
| 5.2.3 | Ensure sudo log file exists | `roles/security/tasks/logging.yml`: `/etc/sudoers.d/99-logfile` `0440`, `Defaults logfile="/var/log/sudo.log"`, validated with `visudo -cf` |
| 5.2.4 | Ensure users must provide password for privilege escalation | Deviation: `ansible` has NOPASSWD (bootstrap); every other sudo user requires a password |
| 5.2.7 | Ensure pam_wheel group is empty and su is restricted to it | Not implemented: no local console login; administrative access is via sudo only (rules `ensure_pam_wheel_group_empty`, `use_pam_wheel_group_for_su`) |
| 5.4.2.5 | Ensure root's PATH does not include world- or group-writable directories | Not implemented: root PATH left as shipped (rule `root_path_all_dirs` flagged) |
| 5.4.3.2 | Ensure default user shell timeout is configured | `roles/security/tasks/system.yml`: `/etc/profile.d/99-tmout.sh` sets `TMOUT=900`, `readonly TMOUT`, `export TMOUT` |
| 5.4.3.3 | Ensure default user umask is configured | `roles/security/tasks/system.yml`: `umask 027` in `/etc/profile.d/99-umask.sh` (login shells) + `UMASK 027` in `/etc/login.defs` + `umask 027` in `/etc/bash.bashrc` (interactive non-login shells) |
| 6.1.2.1.1 | Ensure systemd-journal-remote is installed | Not implemented: no central log host (rule `package_systemd-journal-remote_installed` flagged) |
| 6.1.2.1.2 | Ensure systemd-journal-upload is configured | Not implemented: no remote upload target; `URL`/TLS not configured (rules `systemd_journal_upload_url`, `systemd_journal_upload_server_tls` flagged) |
| 6.1.2.2 | Ensure journald ForwardToSyslog is disabled | `roles/security/tasks/logging.yml`: `ForwardToSyslog=no` in `/etc/systemd/journald.conf` |
| 6.1.2.3 | Ensure journald Compress is configured | `roles/security/tasks/logging.yml`: `Compress=yes` in `/etc/systemd/journald.conf` |
| 6.1.2.4 | Ensure journald Storage is configured | `roles/security/tasks/logging.yml`: `Storage=persistent` in `/etc/systemd/journald.conf` |
| 6.1.3.1 | Ensure rsyslog is installed | Deviation: journald is used (persistent storage, see 6.1.2.4); rsyslog not installed (rule `package_rsyslog_installed` flagged) |
| 6.1.4.1 | Ensure permissions on /var/log are configured | Not implemented: left at distro defaults (rule `permissions_local_var_log` flagged) |
| 6.2.1.1 | Ensure auditd packages are installed | `roles/security/tasks/logging.yml` installs auditd + audispd-plugins |
| 6.2.1.2 | Ensure auditd service is enabled and active | `roles/security/tasks/logging.yml`: service enabled (rules not configured) |
| 6.3.1 | Ensure AIDE is installed and the database is initialized | Not implemented: no file integrity monitoring deployed (rules `package_aide_installed`, `aide_build_database` flagged) |
| 7.2.9 | Ensure local interactive user home directories are configured | `roles/users/tasks/main.yml`: home dirs for managed users (owner = user, no group/world write); stock accounts not audited |
| 7.2.10 | Ensure local interactive user init files are configured | Not implemented: only managed users' home dirs are audited; dotfile permissions left as created (rule `file_permission_user_init_files` flagged) |

## Live audit verification (OpenSCAP / ComplianceAsCode SSG 0.1.81)

Profile `cis_level1_server` on the live server (2026-08-02): 347 rules
evaluated, 292 pass, 55 fail, 61 not applicable; score 73.78%. The failing
rules break down as documented deviations (implemented stricter than the audit
can detect), items intentionally left pending, and unimplemented audit/logging
tooling.

Controls the audit flagged as fail but that are compliant on the live system
(draft content false positives, no fix needed):

| Control | Audit result | Verified state |
|---|---|---|
| 4.1.1 / 4.2.3 / 4.2.4 / 4.2.6 / 4.2.7 / `package_ufw_removed` / `service_nftables_enabled` / `nftables_rules_permanent` / `set_nftables_loopback_traffic` | Fail | ufw active, default deny incoming, rules for 22/80/443, loopback OK (intentional deviation: ufw instead of nftables) |
| 1.1.1.1-1.1.1.5, 1.1.1.9 (kernel modules) | Fail | Modules blocked with `install <mod> /bin/true` (stricter than `blacklist`); SSG's `kernel_module_*` check looks for a literal `blacklist` line |
| 1.5.5 (apport) | Fail | Apport stopped, disabled and `enabled=0`; SSG's `service_apport_disabled` check wants `systemctl mask` |
| 5.1.7 (idle timeout) | Fail | `ClientAliveInterval 300` set; only CountMax differs (stricter, see 5.1.7) |
| 7.2.2 (empty password fields) | Fail | No account has an empty password |
| 2.3.3.1 (chrony) | Fail | Timeserver pools configured |
| 1.1.2.2.1 (/dev/shm) | Fail | Mounted with nodev,nosuid; noexec intentionally not set |

Remaining gaps, intentionally left unimplemented (pending decision, not real
failures):
- PAM hardening (5.3.1 faillock, 5.3.2 pwquality, 5.3.3 pwhistory) and password
  aging (5.4.1.1, 5.4.1.2): SSH is the only login path and is key-based; these
  controls only affect sudo/console password use.
- 5.4.3.1 (nologin not in /etc/shells): already compliant by default, not enforced.
- 1.1.1.6 overlayfs is not blacklisted (Docker requires it); 1.1.1.7 squashfs and
  1.1.1.8 udf are left as-is.
- 1.1.2.1.1 (/tmp partition) and 1.4.1 (bootloader password): not applicable to
  this provider/container host; no console access.
- 1.3.1.1-1.3.1.3 (AppArmor), 6.1.3.1 (rsyslog), 6.1.2.1.1-6.1.2.1.2
  (journal-upload/remote), 6.3.1 (AIDE): tooling for file-integrity and
  central-logging not in scope.
- 6.1.4.1 (/var/log permissions), 5.4.2.5 (root PATH), 7.2.10 (user init file
  permissions): left at distro defaults.
