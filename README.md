# Ansible Role: rsyslog

![GitHub](https://img.shields.io/github/license/jomrr/ansible-role-rsyslog)
![GitHub last commit](https://img.shields.io/github/last-commit/jomrr/ansible-role-rsyslog)
![GitHub issues](https://img.shields.io/github/issues-raw/jomrr/ansible-role-rsyslog)
[![dev](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-rsyslog/dev.yml?branch=dev&label=dev)](https://github.com/jomrr/ansible-role-rsyslog/actions/workflows/dev.yml?query=branch%3Adev)
[![main](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-rsyslog/main.yml?branch=main&label=main)](https://github.com/jomrr/ansible-role-rsyslog/actions/workflows/main.yml?query=branch%3Amain)

Forward the systemd journal and platform log files to a central syslog receiver.

## Purpose

Forward the local systemd journal and text logs to a central syslog receiver.
Set `rsyslog_server` to the collector's DNS name or IP address. The default is
RFC 5424 over TLS on port 6514 with octet-counted framing and server certificate
verification.

## Scope

### Managed

- The rsyslog package, forwarding configuration, persistent sender state and
  enabled rsyslog service.
- Package manager logs on each platform: `/var/log/dpkg.log` and
  `/var/log/apt/history.log` on Debian and Ubuntu, the active `/var/log/dnf.log`
  or `/var/log/dnf5.log` on AlmaLinux and Fedora, and `/var/log/zypp/history`
  and `/var/log/zypper.log` on openSUSE.

### Not Managed

- Journal storage, retention and socket forwarding settings belong to
  jomrr.journald.
- The central receiver and its certificates.

## Requirements

- The packaged rsyslog configuration must include `/etc/rsyslog.d/*.conf`.
  AlmaLinux and Fedora supply the imjournal input in their main configuration.
- The collector must accept the configured transport and framing. For TLS its
  certificate must match rsyslog_server and chain to a trusted CA.

## Dependencies

```yaml
collections:
  - name: community.general
    version: '>=12.0.0'
  - name: ansible.posix
    version: '>=2.0.0'
  - name: containers.podman
    version: '>=1.7.0'
```

## Role Variables

### `rsyslog_server`

Type: `str`. Required: `true`.

DNS name or IP address of the collector. TLS verifies this identity against its
certificate.

### `rsyslog_port`

Type: `int`. Required: `false`.

Destination port on the collector.

Default:

```yaml
rsyslog_port: 6514
```

### `rsyslog_transport`

Type: `str`. Required: `false`.

Send RFC 5424 messages over authenticated TLS or plain TCP.

Default:

```yaml
rsyslog_transport: tls
```

### `rsyslog_ca_file`

Type: `path`. Required: `false`.

Absolute path to a readable PEM trust bundle on the sender. An empty value uses
the platform trust bundle.

Default:

```yaml
rsyslog_ca_file: ''
```

### `rsyslog_additional_files`

Type: `list`. Required: `false`.

Active newline-delimited text logs to monitor in addition to the package manager
logs.

Default:

```yaml
rsyslog_additional_files: []
```

## Managed Files

- `/etc/rsyslog.d/01-central.conf`
- `/etc/apparmor.d/rsyslog.d/central-forwarding (Ubuntu)`
- `/usr/local/sbin/rsyslog-validate-snippet`

## Check Mode

Check mode previews changes on hosts with the rsyslog package and service
account already installed.

## Service Behavior

Install, enable and start rsyslog. Reapplying the same settings leaves the
running service in place.

### Handlers

- Restart rsyslog after a change to the forwarding configuration or journal
  access.

## Operational Notes

- Journal collection uses imjournal directly, including when ForwardToSyslog is
  disabled. Local socket and kernel inputs continue through the distribution's
  rules. On Ubuntu the syslog account joins systemd-journal.
- imfile tags each line with the file basename, facility local0 and severity
  info. An absent file can appear later. Use paths to active text files readable
  by rsyslog. Exclude rotated archives, binary login databases and local syslog
  outputs such as /var/log/messages, /var/log/syslog and /var/log/auth.log to
  avoid duplicate events.
- Input positions persist across daemon restarts. Existing file content is
  eligible on first discovery. A disk-assisted queue buffers messages during a
  collector outage with a 256 MiB spool limit and retries when the receiver
  returns.
- Plain TCP uses newline framing and sends log data in cleartext. Set
  rsyslog_port to the collector's TCP port when selecting this transport.

## Supported Platforms

| OS Family | Distribution | Version | Container Image |
| --------- | ------------ | ------- | --------------- |
| RedHat | AlmaLinux | latest | [jomrr/molecule-almalinux:latest](https://hub.docker.com/r/jomrr/molecule-almalinux) |
| Debian | Debian | latest | [jomrr/molecule-debian:latest](https://hub.docker.com/r/jomrr/molecule-debian) |
| RedHat | Fedora | latest | [jomrr/molecule-fedora:latest](https://hub.docker.com/r/jomrr/molecule-fedora) |
| Suse | OpenSuse Leap | latest | [jomrr/molecule-opensuse-leap:latest](https://hub.docker.com/r/jomrr/molecule-opensuse-leap) |
| Suse | OpenSuse Tumbleweed | latest | [jomrr/molecule-opensuse-tumbleweed:latest](https://hub.docker.com/r/jomrr/molecule-opensuse-tumbleweed) |
| Debian | Ubuntu | latest | [jomrr/molecule-ubuntu:latest](https://hub.docker.com/r/jomrr/molecule-ubuntu) |

## Example Playbook

### Forward the journal and package manager logs

```yaml
---
- name: Configure central logging
  hosts: all
  gather_facts: true
  roles:
    - role: jomrr.rsyslog
      rsyslog_server: logs.example.org
```

### Trust a private collector CA and include an application log

```yaml
---
- name: Forward application and system logs
  hosts: app_servers
  gather_facts: true
  roles:
    - role: jomrr.rsyslog
      rsyslog_server: logs.internal.example.org
      rsyslog_ca_file: /etc/ssl/certs/internal-logging-ca.pem
      rsyslog_additional_files:
        - /var/log/myapp/events.log
```

## References

- [Journal input](https://docs.rsyslog.com/doc/configuration/modules/imjournal.html)
- [Text file input](https://docs.rsyslog.com/doc/configuration/modules/imfile.html)
- [Remote forwarding](https://docs.rsyslog.com/doc/configuration/modules/omfwd.html)

## Author

[Jonas Mauer](https://github.com/jomrr)

## License

This project is licensed under the MIT License.
See [LICENSE](LICENSE) for the full license text.

Copyright (c) 2026 Jonas Mauer.
