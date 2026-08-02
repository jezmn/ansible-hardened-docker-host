# Getting Started

## Requirements

- A Linux environment to run Ansible from
- `ansible`, `git`, `sshpass`, `whois`, `python3-venv`

```bash
sudo apt update && sudo apt install -y ansible git sshpass whois python3-venv
```

## 1. Clone and configure

```bash
git clone https://github.com/jezmn/ansible-hardened-docker-host.git
cd ansible-hardened-docker-host

# Install Ansible dependencies
ansible-galaxy collection install -r requirements.yml

# Copy inventory examples
cp inventories/hosts-bootstrap.ini.example inventories/hosts-bootstrap.ini
cp inventories/hosts.ini.example inventories/hosts.ini
```

## 2. Accept SSH fingerprint

`<provider-login>` is the login your provider gives you: `root` on most
providers, `ubuntu` on AWS, and so on.

```bash
ssh <provider-login>@<server_ip>   # type "yes", then exit
# or: ssh-keyscan -H <server_ip> >> ~/.ssh/known_hosts
```

## 3. Bootstrap

#### If your provider uses an SSH key instead of a password

On most clouds you upload a public key when creating the server,
and the provider installs it in the login user's `authorized_keys`. Two
keypairs are in play. Don't mix them up:

| Keypair | Private key path | Public key |
|---|---|---|
| `~/.ssh/provider_ed25519` | `hosts-bootstrap.ini` (`ansible_ssh_private_key_file`) | uploaded to your provider |
| `~/.ssh/ansible_ed25519` | `hosts.ini` (`ansible_ssh_private_key_file`) | `group_vars/bootstrap.yml` |

#### Configure the bootstrap inventory

Edit `inventories/hosts-bootstrap.ini` with your server IP and provider
login:

```ini
# Edit with your server IP
[bootstrap]
<server_ip>

[bootstrap:vars]
ansible_user=root    # your provider login (ubuntu, etc.)
ansible_python_interpreter=/usr/bin/python3

# Provider login key, uncomment if it uses a key
# ansible_ssh_private_key_file=~/.ssh/provider_ed25519
```

Verify Ansible can reach the server (drop -k if it uses a key):

```bash
ansible bootstrap -i inventories/hosts-bootstrap.ini -m ping -k
```
Generate the `ansible` provisioning user's keypair. This user is what
`site.yml` connects as, whatever initial login your provider gives you:

```bash
ssh-keygen -t ed25519 -C "ansible" -f ~/.ssh/ansible_ed25519
```
Put the public key (`~/.ssh/ansible_ed25519.pub`) in
`inventories/group_vars/bootstrap.yml`:

```yaml
bootstrap_user:
  name: ansible
  ssh_public_key: "<ssh_public_key>"
```

Run:

```bash
ansible-playbook -i inventories/hosts-bootstrap.ini playbooks/bootstrap.yml -k
```

This creates the `ansible` user and installs your key on the server.

## 4. Configure the inventory

Edit `inventories/hosts.ini` with your server IP:

```ini
# Edit with your server IP
[servers]
<server_ip>

[servers:vars]
ansible_user=ansible    # ansible user from step 3
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=~/.ssh/ansible_ed25519
```

## 5. Configure variables

Edit `inventories/group_vars/servers/users.yml` with your accounts:

```yaml
users_accounts:
  - name: <username>
    sudo: true
    ssh_public_key: "<ssh_public_key>"    # user key from ssh-keygen
```

Edit `inventories/group_vars/servers/vault.yml` with password hashes:

```yaml
users_passwords:
  <username>: "<hash>"
```

Generate hashes:

```bash
mkpasswd --method=sha-512
```

Encrypt the vault file (it stores password hashes):

```bash
ansible-vault encrypt inventories/group_vars/servers/vault.yml
```

The `--ask-vault-pass` in the playbook command asks for this password.

## 6. Run playbook

Before running, open an SSH session to your server and keep it open in case
you get locked out.

Dry-run first to see what will change.

```bash
ansible-playbook -i inventories/hosts.ini playbooks/site.yml --check --diff --ask-vault-pass
```

Run it:

```bash
ansible-playbook -i inventories/hosts.ini playbooks/site.yml --ask-vault-pass
```

## 7. Linting

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ansible-lint
ansible-lint
```
