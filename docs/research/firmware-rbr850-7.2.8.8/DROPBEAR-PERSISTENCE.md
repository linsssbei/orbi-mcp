# Dropbear persistence investigation

> Historical research from 2026-10-27–29; consolidated on 2026-11-01.
> Use the [current MCP guide](../../../README.md) for supported setup and behavior.
> Earlier implementation status below describes the investigation date.
> Device MACs, key fingerprints and personal home paths are replaced with placeholders.
> Evidence and firmware links require the [local research archive](../README.md);
> they are excluded from Git and the npm package. Run repository-relative commands from the repo root.

Exact firmware: **RBR850 V7.2.8.8_5.1.24**. Inspected extracted firmware and
the live router using read-only SSH commands. No boot configuration was changed
and no additional reboot was performed.

## Finding

The enrolled key and generated host key are already on persistent flash.
Dropbear is not configured to restart automatically in the inspected setup.
A small startup addition can launch it after boot, without the admin password
or another SeAL enrollment request. A reboot test remains necessary to confirm
the complete behavior after such a change.

## Persistent storage: confirmed live

`rootfs/lib/preinit/80_mount_root`, lines 54–65, mounts the flash-backed volumes
and creates the root overlay with:

```text
upperdir=/tmp/media/reserved2/overlay/upper
```

The live mount table confirms `/tmp/media/reserved2` is **UBIFS on
ubi2:Reserved**, and `/` uses that directory as its overlay upper layer.
Although the path starts with `/tmp`, this mounted filesystem is persistent
flash rather than the surrounding temporary RAM filesystem.

Live files exist at both their normal paths and in the overlay upper layer:

- `/etc/dropbear/authorized_keys`
- `/etc/dropbear/dropbear_rsa_host_key`
- `/tmp/media/reserved2/overlay/upper/etc/dropbear/authorized_keys`
- `/tmp/media/reserved2/overlay/upper/etc/dropbear/dropbear_rsa_host_key`

Both authorized-key paths have SHA256
`<recorded-authorized-key-file-sha256>`.
The host-key files have mode 0600. Their private contents were not read.
The enrolled shell-list change is also present: `/etc/shells` lists `/bin/sh`.

## Automatic startup: missing

The firmware inventory and live router contain:

```text
/etc/rc.d/S19dropbear -> ../init.d/dropbear
/etc/rc.d/K50dropbear -> ../init.d/dropbear
```

However, **`/etc/init.d/dropbear` does not exist** in either the image or the
live router. These dangling links cannot start or stop the service. Having
`/etc/config/dropbear` present does not create the missing service script.
The SeAL enrollment handler only starts a process; it installs no boot service.

## Available startup hooks

The firmware provides two relevant mechanisms:

1. `/etc/init.d/done` has `START=95`, and `/etc/rc.d/S95done` points to it. Its
   boot function explicitly runs `sh /etc/rc.local` if that file exists.
   The live `/etc/rc.local` currently contains only comments and `exit 0`.
2. `/etc/init.d/boot` mounts `/opt/cache` and `/opt/persistent`, then calls
   `seal boot`. `/usr/bin/seal`, lines 150–151, runs executable
   `/opt/cache/boothook.sh` and `/opt/persistent/boothook.sh` if present.
   Neither hook currently exists. This is an earlier startup phase (`START=10`).

The live `done`, `rc.local`, `seal` and `80_mount_root` files have the same
SHA256 hashes as their counterparts in the downloaded firmware.

## Recommended change, not applied

Add a guarded Dropbear launch **before `exit 0` in `/etc/rc.local`**. This late
hook runs after the normal network (`S20network`), account initialization
(`S61acos_rc`) and firewall script (`S90firewall_script.sh`) in the ordered boot
sequence. Use the enrolled key and existing host key, with password login
disabled. Bind the listener to the router's LAN IPv4 address, currently
`192.168.1.1`, rather than a wildcard address. Avoid starting a second process
if Dropbear is already running. No password or private client key needs to be
stored on the router.

The corresponding launch would use the existing supported arguments:

```sh
/usr/sbin/dropbear -P /var/run/dropbear.pid -s -g \
    -p 192.168.1.1:22 -K 300 -T 3 -R
```

`-R` permits generation of a missing host key; it does not delete the existing
one. Preserve that existing key so the pinned host identity stays consistent.
An administrator changing the LAN address would also need to update a startup
command bound to that specific address.

Validation after applying a boot change should be one normal reboot followed
by SSH authentication with the existing client key and strict host-key checking,
without sending another enrollment request or retrieving the admin password.
Roll back by removing only the added startup block from `rc.local`.

These findings concern ordinary reboot behavior. Firmware upgrades, factory
resets and flash-volume recovery follow different paths and are not covered by
a successful ordinary-reboot test.

Live evidence: `evidence/dropbear-persistence-live.json`.
