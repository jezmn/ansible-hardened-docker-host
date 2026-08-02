import re


def test_sshd_config_restored_from_backup(host):
    config = host.file("/etc/ssh/sshd_config")
    backup = host.file("/etc/ssh/sshd_config.ansible-backup")
    assert config.exists
    assert backup.exists
    assert config.content_string == backup.content_string


def test_sshd_config_mode_0600(host):
    assert host.file("/etc/ssh/sshd_config").mode == 0o600


def test_sshd_damage_reverted(host):
    config = host.file("/etc/ssh/sshd_config").content_string
    assert not re.search(r"^PasswordAuthentication yes", config, re.M)


def test_sshd_config_parses(host):
    result = host.run("sshd -T")
    assert result.rc == 0
