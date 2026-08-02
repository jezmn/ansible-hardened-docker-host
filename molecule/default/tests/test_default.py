import re


def test_user_exists(host):
    assert host.user("alice").exists


def test_ssh_key_installed(host):
    key = host.file("/home/alice/.ssh/authorized_keys")
    assert key.exists


def test_sshd_password_auth_disabled(host):
    config = host.file("/etc/ssh/sshd_config")
    assert "PasswordAuthentication no" in config.content_string


def test_sshd_forwarding_disabled(host):
    config = host.file("/etc/ssh/sshd_config")
    assert "AllowTcpForwarding no" in config.content_string
    assert "AllowAgentForwarding no" in config.content_string
    assert "X11Forwarding no" in config.content_string


def test_docker_installed(host):
    assert host.package("docker-ce").is_installed


def test_docker_cleanup_cron(host):
    assert "docker cleanup" in host.check_output("crontab -l")


def test_fail2ban_jail_configured(host):
    jail = host.file("/etc/fail2ban/jail.local")
    assert jail.exists
    assert "[sshd]" in jail.content_string


def test_sshd_restored_after_rollback(host):
    config = host.file("/etc/ssh/sshd_config")
    assert not re.search(r"^PasswordAuthentication yes", config.content_string, re.M)
