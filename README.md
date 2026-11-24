# Ansible Role: rsyslog

![GitHub](https://img.shields.io/github/license/jomrr/ansible-role-rsyslog)
![GitHub last commit](https://img.shields.io/github/last-commit/jomrr/ansible-role-rsyslog)
![GitHub issues](https://img.shields.io/github/issues-raw/jomrr/ansible-role-rsyslog)
[![dev](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-rsyslog/dev.yml?branch=dev&label=dev)](https://github.com/jomrr/ansible-role-rsyslog/actions/workflows/dev.yml?query=branch%3Adev)
[![main](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-rsyslog/main.yml?branch=main&label=main)](https://github.com/jomrr/ansible-role-rsyslog/actions/workflows/main.yml?query=branch%3Amain)

Install and run rsyslog locally with optional forwarding to a central receiver.

## Purpose

Install rsyslog, enable the service at boot and run the distribution's local
logging configuration. Set `rsyslog_server` to also forward the systemd journal
to a collector. The sender uses TLS on port 6514 and verifies the receiver
against the system trust store by default.

## Scope

### Managed

- The enabled rsyslog service, its GnuTLS module and the system CA certificates
  on every host.
- With a receiver configured, a forwarding drop-in, a disk-assisted queue, and
  any explicitly selected text log inputs.

### Not Managed

- Journal storage, retention and socket forwarding settings belong to
  jomrr.journald.
- The receiver, certificate issuance and distribution-owned local logging rules.

## Requirements

- Forwarding uses the packaged include of `/etc/rsyslog.d/*.conf`. AlmaLinux and
  Fedora provide the imjournal input in their main configuration.
- Both transports use RFC 5424 messages with octet-counted framing. Configure
  plain TCP receivers for RFC 6587 octet counting. When the sender trusts only
  the root CA, the TLS receiver must present its leaf certificate followed by
  every required intermediate.
- For mutual TLS, provision the client certificate chain and matching private
  key on the sender. Allow rsyslog to read the files and restrict key access to
  its service identity and administrators. Configure the receiver to require
  client certificates and authorize the intended senders.

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

### `rsyslog_backup`

Type: `bool`. Required: `false`.

Back up the forwarding drop-in, AppArmor extension and validation helper before
replacing their contents.

Default:

```yaml
rsyslog_backup: true
```

### `rsyslog_server`

Type: `str`. Required: `false`.

A receiver hostname or IP address enables forwarding. Omit the variable or
supply an empty string for local operation.

### `rsyslog_forward_only`

Type: `bool`. Required: `false`.

When forwarding is enabled, stop all messages in the default ruleset before the
distribution's local logging rules.
The forwarding queue still buffers records when the receiver is offline.

Default:

```yaml
rsyslog_forward_only: false
```

### `rsyslog_transport`

Type: `str`. Required: `false`.

Send octet-counted RFC 5424 messages over authenticated TLS or plain TCP.

Default:

```yaml
rsyslog_transport: tls
```

### `rsyslog_port`

Type: `int`. Required: `false`.

Override the destination port. The default is 6514 for TLS and 514 for plain
TCP.

### `rsyslog_ca_file`

Type: `path`. Required: `false`.

Absolute path to a readable PEM trust bundle on the sender. An empty value uses
the platform trust bundle.

Default:

```yaml
rsyslog_ca_file: ''
```

### `rsyslog_client_cert_file`

Type: `path`. Required: `false`.

Absolute path to the sender's PEM certificate chain for mutual TLS. Set together
with rsyslog_client_key_file.

Default:

```yaml
rsyslog_client_cert_file: ''
```

### `rsyslog_client_key_file`

Type: `path`. Required: `false`.

Absolute path to the matching PEM private key on the sender.

Default:

```yaml
rsyslog_client_key_file: ''
```

### `rsyslog_permitted_peers`

Type: `list`. Required: `false`.

Accepted receiver certificate identities. Defaults to a list containing
rsyslog_server when forwarding is enabled.

### `rsyslog_min_severity`

Type: `str`. Required: `false`.

Least urgent severity forwarded. For example, warning includes emerg through
warning.

Default:

```yaml
rsyslog_min_severity: info
```

### `rsyslog_queue_max_disk_space`

Type: `str`. Required: `false`.

Disk budget for the forwarding queue. Supply a positive byte count or an rsyslog
size such as 256m.

Default:

```yaml
rsyslog_queue_max_disk_space: 256m
```

### `rsyslog_platform_files`

Type: `list`. Required: `false`.

Paths to active platform logs selected in inventory, such as /var/log/dpkg.log.

Default:

```yaml
rsyslog_platform_files: []
```

### `rsyslog_additional_files`

Type: `list`. Required: `false`.

Each entry is an absolute text file path or a mapping with a required path and
optional tag and facility. Defaults are the file basename and local0. The first
mapping for a path takes precedence over plain path entries.

Default:

```yaml
rsyslog_additional_files: []
```

## Managed Files

- `/etc/rsyslog.d/01-central.conf`
- `/etc/apparmor.d/rsyslog.d/central-forwarding`
- `/usr/local/sbin/rsyslog-validate-snippet`

## Check Mode

Check mode previews changes on hosts with the rsyslog package and service
account already installed.

## Service Behavior

Removing rsyslog_server or setting it to an empty string removes the role's
forwarding drop-in, Ubuntu AppArmor extension and validation helper. rsyslog
continues running with the local rules. The role validates the assembled
configuration before starting the service. Applying the same settings again
keeps the running service in place.

### Handlers

- Validate the assembled configuration and restart rsyslog when the managed
  configuration or journal access changes.

## Operational Notes

- Journal forwarding uses imjournal directly, even with ForwardToSyslog
  disabled. By default, Red Hat also writes journal events to files such as
  /var/log/messages and /var/log/secure. Debian and Ubuntu can write copies from
  socket and kernel inputs. Adding those files as forwarding inputs can
  duplicate events at the collector.
- Set `rsyslog_forward_only: true` together with `rsyslog_server` for a pure
  forwarder. After journal forwarding, all messages in the default ruleset stop
  before subsequent rules, including socket and kernel messages and records
  below the forwarding severity threshold. Journald keeps its configured
  retention. Selected text files still feed the forwarding queue, which buffers
  undelivered records locally using the configured disk budget. Removing the
  receiver restores the distribution's local logging.
- File collection is opt-in on every platform. To forward DNF, APT or Zypper
  logs, list the active files in rsyslog_platform_files for the relevant
  inventory group. imfile assigns severity info; a threshold of notice or higher
  urgency omits file records.
- Select newline-delimited text files readable by the service. SELinux may deny
  reads by syslogd_t for nonstandard paths or labels. Check recent audit denials
  on the sender with `ausearch -m avc -ts recent | grep rsyslog`.
- The disk queue retries delivery during an outage. Disabling forwarding
  preserves queued messages and input positions. Re-enabling uses that state, so
  pending messages can go to the newly configured receiver. On Ubuntu, syslog
  retains any systemd-journal group membership previously granted for journal
  access.

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

### Run the local syslog service

```yaml
---
- name: Enable local logging
  hosts: all
  roles:
    - role: jomrr.rsyslog
```

### Forward the journal over TLS

```yaml
---
- name: Configure central logging
  hosts: all
  roles:
    - role: jomrr.rsyslog
      rsyslog_server: logs.example.org
```

### Use the journal as the local record and buffer remote delivery

```yaml
---
- name: Configure a pure forwarder
  hosts: all
  roles:
    - role: jomrr.rsyslog
      rsyslog_server: logs.example.org
      rsyslog_forward_only: true
```

### Authenticate a sender and select application logs

```yaml
---
- name: Forward application and system logs
  hosts: app_servers
  roles:
    - role: jomrr.rsyslog
      rsyslog_server: 192.0.2.10
      rsyslog_permitted_peers: [logs.internal.example.org]
      rsyslog_ca_file: /etc/ssl/certs/internal-logging-ca.pem
      rsyslog_client_cert_file: /etc/rsyslog.d/pki/sender.pem
      rsyslog_client_key_file: /etc/rsyslog.d/pki/sender.key
      rsyslog_queue_max_disk_space: 512m
      rsyslog_additional_files:
        - /var/log/myapp/events.log
        - path: /var/log/myapp/access.log
          tag: myapp-access
          facility: local1
```

## References

- [Journal input](https://docs.rsyslog.com/doc/configuration/modules/imjournal.html)
- [Text file input](https://docs.rsyslog.com/doc/configuration/modules/imfile.html)
- [Remote forwarding](https://docs.rsyslog.com/doc/configuration/modules/omfwd.html)
- [Syslog over TCP](https://www.rfc-editor.org/rfc/rfc6587.html)

## Author

[Jonas Mauer](https://github.com/jomrr)

## License

This project is licensed under the MIT License.
See [LICENSE](LICENSE) for the full license text.

Copyright (c) 2026 Jonas Mauer.
