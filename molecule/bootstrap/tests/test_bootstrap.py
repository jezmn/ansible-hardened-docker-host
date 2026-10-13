def test_user_exists(host):
    assert host.user("ansible").exists


def test_ansible_user_in_sudo_group(host):
    assert "sudo" in host.user("ansible").groups


def test_ssh_key_installed(host):
    key = host.file("/home/ansible/.ssh/authorized_keys")
    assert key.exists


def test_passwordless_sudo(host):
    sudoers = host.file("/etc/sudoers.d/ansible")
    assert sudoers.exists
    assert "NOPASSWD" in sudoers.content_string


def test_sudo_installed(host):
    assert host.package("sudo").is_installed


def test_bootstrap_sudoers_valid(host):
    result = host.run("/usr/sbin/visudo -cf /etc/sudoers.d/ansible")
    assert result.rc == 0
