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
- Rate limiting for the active rsyslog journal input.
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

Back up managed files before changing their contents, including the Red Hat
journal input configuration.

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

### `rsyslog_imjournal_ratelimit_interval`

Type: `int`. Required: `false`.

Rate-limit window in seconds for the rsyslog journal input. Set to 0 to disable
its rate limit.

Default:

```yaml
rsyslog_imjournal_ratelimit_interval: 600
```

### `rsyslog_imjournal_ratelimit_burst`

Type: `int`. Required: `false`.

Maximum number of journal records accepted per window. Ignored when the interval
is 0.

Default:

```yaml
rsyslog_imjournal_ratelimit_burst: 20000
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

### `rsyslog_keepalive`

Type: `bool`. Required: `false`.

Enable TCP keepalive probes on the forwarding connection for both TLS and plain
TCP.

Default:

```yaml
rsyslog_keepalive: false
```

### `rsyslog_keepalive_time`

Type: `int`. Required: `false`.

Idle time in seconds before the first probe when keepalive is enabled. Use 1 to
32767, or 0 for the kernel default.

Default:

```yaml
rsyslog_keepalive_time: 0
```

### `rsyslog_keepalive_interval`

Type: `int`. Required: `false`.

Seconds between unanswered probes when keepalive is enabled. Use 1 to 32767, or
0 for the kernel default.

Default:

```yaml
rsyslog_keepalive_interval: 0
```

### `rsyslog_keepalive_probes`

Type: `int`. Required: `false`.

Number of unanswered probes before Linux closes the connection. Use 1 to 127, or
0 for the kernel default, when keepalive is enabled.

Default:

```yaml
rsyslog_keepalive_probes: 0
```

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

### `rsyslog_excluded_programs`

Type: `list`. Required: `false`.

Skip remote forwarding for journal and file records whose rsyslog programname
exactly matches a listed name. Matching is case-sensitive.

Default:

```yaml
rsyslog_excluded_programs: []
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

Absolute paths or glob patterns for active platform logs, such as
/var/log/dpkg.log.

Default:

```yaml
rsyslog_platform_files: []
```

### `rsyslog_additional_files`

Type: `list`. Required: `false`.

Each entry is an absolute path or glob pattern, or a mapping with a required
path and optional tag, facility and timestamp. All matches share the configured
tag and facility. The defaults are the basename of the configured path or
pattern and local0. The first mapping for a path takes precedence over plain
path entries.
timestamp.format selects access, apache_error, nginx_error, sssd or iso8601.
Optional regex selects capture group 1 of a POSIX extended expression, or field
selects a top-level JSON key. timezone defaults to UTC for timestamps without an
offset. Unparseable records retain the imfile read time.

Default:

```yaml
rsyslog_additional_files: []
```

## Managed Files

- `/etc/rsyslog.d/00-imjournal.conf`
- `/etc/rsyslog.d/01-central.conf`
- `/etc/rsyslog.d/central-timezones.json`
- `/etc/apparmor.d/rsyslog.d/central-forwarding`
- `/usr/local/sbin/rsyslog-validate-snippet`

## Check Mode

Check mode previews changes on hosts with the rsyslog package and service
account already installed.

## Service Behavior

Removing rsyslog_server or setting it to an empty string removes the role's
forwarding drop-in and Ubuntu AppArmor extension. The validation helper is
removed when no managed rsyslog drop-in needs it. rsyslog continues running with
the local rules. The role validates the assembled configuration before starting
the service. Applying the same settings again keeps the running service in
place.

### Handlers

- Validate the assembled configuration and restart rsyslog when the managed
  configuration or journal access changes.

## Operational Notes

- TCP keepalive is off by default. With 60 seconds of idle time, a 15-second
  interval and 4 unanswered probes, Linux can detect an unreachable peer on an
  idle forwarding connection in about 2 minutes. Subsequent delivery uses
  omfwd's existing retry queue. If the TCP send queue already holds
  unacknowledged data, TCP retransmission timers determine when the connection
  fails.
- On the collector host, set `rsyslog_excluded_programs: [loki]` to keep Loki's
  own messages in the local journal and avoid sending them back to Loki. The
  filter compares the rsyslog `programname` before queuing a message for
  forwarding. For text file inputs, rsyslog derives this name from the input
  tag.
- By default imjournal accepts 20000 records per 600 seconds. Records it
  discards never reach the forwarding queue. Set
  `rsyslog_imjournal_ratelimit_interval: 0` to read without this limit, or tune
  `rsyslog_imjournal_ratelimit_burst` for a finite window.
- Each parameter at its default is omitted. On AlmaLinux and Fedora, the
  distribution loads imjournal and then reads the role's rate-limit overrides
  from `/etc/rsyslog.d/00-imjournal.conf` in both local and forwarding mode.
  Restoring both defaults removes this drop-in. On Debian, Ubuntu and openSUSE,
  the role sets overrides on its own imjournal module when forwarding is
  enabled. Journald has its own rate limits.
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
- imfile matches `*`, `?` and bracket expressions such as `[0-9]` or `[!ab]` in
  directory and file names. Set a tag on the pattern to give every matching file
  the same sender tag. For example, `/var/log/sssd/*.log` can use `sssd`.
- Set an input's timestamp.format to access (Apache or nginx), apache_error,
  nginx_error, sssd or iso8601 to put the event time in the RFC 5424 header. The
  message body retains the original line. The standard log layouts work
  directly. For a different location, set timestamp.regex to a POSIX extended
  expression whose first capture group contains the entire timestamp, or set
  timestamp.field to a top-level JSON key such as @timestamp. Each file must
  contain one event per line.
- An offset in the line takes precedence. For timestamps without one,
  timestamp.timezone accepts UTC (default), a signed offset such as +05:30 or an
  IANA name such as Europe/Berlin. For named zones, the Ansible controller needs
  tzdata and zdump with -i support. Run the role again after a timezone database
  update. During the repeated autumn hour the earlier instant is used.
  Nonexistent local times, invalid dates, missing fields and unconfigured inputs
  use the imfile read time. RFC 5424 carries up to six fractional digits.
- Enabling or removing the last timestamp parser switches the forwarding spool.
  Pending records drain with their original header format. During a switch with
  a backlog, both spools can use disk space up to rsyslog_queue_max_disk_space
  each.
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

### Forward the journal over TLS with TCP keepalive

```yaml
---
- name: Configure central logging
  hosts: all
  roles:
    - role: jomrr.rsyslog
      rsyslog_server: logs.example.org
      rsyslog_keepalive: true
      rsyslog_keepalive_time: 60
      rsyslog_keepalive_interval: 15
      rsyslog_keepalive_probes: 4
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
      rsyslog_imjournal_ratelimit_interval: 0
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
        - path: /var/log/sssd/*.log
          tag: sssd
          facility: local1
          timestamp: { format: sssd, timezone: Europe/Berlin }
        - path: /var/log/nginx/access.log
          timestamp: { format: access }
        - path: /var/log/myapp/events.jsonl
          timestamp: { format: iso8601, field: '@timestamp' }
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
