# Pterodactyl Eggs

Pterodactyl eggs maintained by Bedrock-Phanatics.

| Egg | File |
| --- | --- |
| [Quark](#quark-egg) | `quark-pterodactyl-egg.json` |
| [Bifrost](#bifrost-egg) | `bifrost-pterodactyl-egg.json` |

## Quark Egg

A Pterodactyl egg for running [Quark](https://github.com/Bedrock-Phanatics/Quark), a high-performance Minecraft: Bedrock server software based on PocketMine-MP and Axolotl.

Quark is designed around performance, efficiency, and greater use of native C/C++ extensions while maintaining compatibility with the PocketMine-MP ecosystem where possible.

### Requirements

This egg is specifically built for:

* **Quark / PocketMine-MP 5**
* **PHP 8.4**
* **Linux x86_64**
* **Pterodactyl Panel**

Other PocketMine versions and PHP versions are not supported by this egg.

### PHP Runtime

The egg uses the custom PHP 8.4 PM5 binaries maintained by Bedrock-Phanatics:

[Bedrock-Phanatics/PHP-Binaries](https://github.com/Bedrock-Phanatics/PHP-Binaries)

Specifically:

```text
pm5-php-8.4-latest
```

### Installation

1. Download the latest `quark-pterodactyl-egg.json`.
2. Open your Pterodactyl admin panel.
3. Navigate to:

```text
Nests → Import Egg
```

4. Import the JSON file.
5. Create a server using the Quark egg.
6. Start the server.

The installation script will automatically:

* Download the required PHP 8.4 PM5 runtime
* Configure the PHP extension directory
* Download Composer
* Clone the latest Quark `stable` branch
* Build the Quark server PHAR
* Create the required server directories and files

### Startup

Quark is started using:

```bash
./bin/php7/bin/php ./PocketMine-MP.phar --no-wizard
```

### Updating Quark

Reinstalling the server through Pterodactyl will fetch and build the latest version of the Quark `stable` branch.

Back up your server data before reinstalling.

Important directories include:

```text
plugins/
players/
worlds/
resource_packs/
```

Along with your server configuration files.

### Architecture Support

Currently, this egg supports:

```text
Linux x86_64
```

The installer will stop if an unsupported architecture is detected instead of attempting to use an incompatible PHP binary.

### Related Projects

#### Quark

High-performance Minecraft: Bedrock server software leveraging PHP, C, and C++ to push PocketMine-MP to its limits.

https://github.com/Bedrock-Phanatics/Quark

#### PHP Binaries

Custom PocketMine-MP PHP builds used by Quark.

https://github.com/Bedrock-Phanatics/PHP-Binaries

### Disclaimer

Quark is a fork of PocketMine-MP and Axolotl and is not affiliated with Mojang Studios or Microsoft.

Minecraft is a trademark of Microsoft Corporation.

## Bifrost Egg

`bifrost-pterodactyl-egg.json` runs [Bifrost](https://github.com/TrixNEW/Bifrost), the Bedrock NetherNet proxy,
on the [Zig 0.17.0 runtime](https://github.com/TrixNEW/pterodactyl-zig) (`ghcr.io/trixnew/pterodactyl-zig:0.17.0`).
Linux x86_64 only, as Bifrost is.

### Installation

1. Import `bifrost-pterodactyl-egg.json` under **Nests → Import Egg**.
2. Create a server with at least 2 GiB of disk for the temporary build. The installer gets the server's memory or
   Wings' installer limit (1 GiB by default), whichever is larger; 1 GiB is enough.
3. Set **Bifrost Version** to a tag or full 40-character commit hash for production. `main` is the default.
4. Wait for the install (several minutes), then start the server.

The installer runs in `debian:trixie-slim`, the same Debian release as the runtime image, so the native library
uses the runtime's libstdc++. It:

- downloads Zig 0.17.0 and verifies its minisign signature,
- fetches Bifrost at the chosen revision and runs `tools/setup-native.sh` to build the patched libdatachannel,
- builds with `zig build -Doptimize=ReleaseSafe` (the **Build Mode** variable, admin only),
- checks every shared library resolves, then starts and stops the new build once,
- only then replaces `bifrost/` (`bin/bifrost`, `lib/libdatachannel.so*`, `BUILD` with the commit).

The build directory `.bifrost-build/` is removed afterwards. Wings marks installs successful whatever the script
returns, so a failed install prints `Bifrost installation FAILED` and leaves the previous build untouched. On a
first install the server then refuses to start with "Bifrost is not installed".

Startup runs `./bifrost/bin/bifrost` directly with `LD_LIBRARY_PATH=/home/container/bifrost/lib`. Nothing is
compiled or downloaded at startup apart from the optional key refresh below. The stop command sends `SIGINT`,
which Bifrost handles by shutting down gracefully.

### Updating

Change **Bifrost Version** if needed and **Reinstall**. Reinstalling only replaces `bifrost/`,
`config/bifrost.example.toml` and `minecraft-keys.json`. It never touches `config/bifrost.toml`, `plugins/`, `bifrost-identity.der` or
`bifrost-proxy.key`. Back them up anyway.

### Configuration

The first install writes `config/bifrost.toml` for the recommended production setup: managed sessions with Xbox
authentication (`[auth] mode = "verify"`). After that the file is yours. The only line the panel rewrites, on
every start, is `bind = "0.0.0.0:<primary port>"`. `config/bifrost.example.toml` is upstream's fully commented
reference for the installed revision.

**Initial Backend** sets the first `[[backend]]` address when the file is created. The default, `172.18.0.1:19133`,
is the Wings Docker gateway, which reaches a backend allocated on `172.18.0.1` on the same node.

On first start Bifrost creates `bifrost-identity.der` and `bifrost-proxy.key` (mode 0600) and logs:

```
managed sessions; backends must trust proxy key MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAE...
```

#### Microsoft signing keys

`[auth] mode = "verify"` needs `minecraft-keys.json`. The installer downloads it, and with **Refresh Xbox Keys**
set to `1` (default) every start downloads it again, replacing the file only when the download succeeds and starts
like Microsoft's key set (`{"keys":[`). Otherwise the saved copy is used. Microsoft rotates the keys, so restart now and then (daily is plenty).
If you set a different `keys_file`, refresh it yourself.

#### Plugins

Copy Bifrost native plugin libraries (`.so`) into `plugins/` and restart. Zig, C and C++ plugins need no extra
runtime libraries. The egg doesn't install Bifrost's example plugins.

### Networking

| Port | Protocol | Use |
| --- | --- | --- |
| primary allocation | TCP | NetherNet HTTP signaling, the address players add |
| primary allocation | UDP | WebRTC for players and backends |

Wings publishes every allocation on both TCP and UDP, so the default config needs only the primary allocation:
`port_min = port_max = <primary port>` with `udp_mux = true` shares one UDP socket for all connections. Players
reach the container through Docker NAT, so the config adds a STUN server to `ice_servers` to advertise the public
address.

Upstream hasn't tried `udp_mux` with vanilla clients. To use a port range instead, add a contiguous block of
allocations (one port per connection, and each player uses two: one to the player, one to the backend), then set
`port_min`/`port_max` to it and `udp_mux = false`. These two lines are only written on first install, so update them
if you change the primary allocation.

### Running in front of Quark

1. Put Quark (v6, `acad4380b` or newer; `a2cf1f81e` or newer for real IPs) on an allocation that isn't public,
   such as `172.18.0.1:19133`, with `xbox-auth = true`.
2. Copy the proxy key Bifrost logs into Quark's `server.toml`:

   ```toml
   [network]
   trusted-proxy-keys = ["MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAE..."]
   ```

3. Stop players bypassing Bifrost: only Bifrost should reach Quark's signaling port and UDP ports. An allocation
   on the Docker gateway address isn't reachable from outside the node. Otherwise block it in the host firewall
   (`DOCKER-USER` chain). Bypassing skips Bifrost's plugins and limits; logins are still verified by Quark.

Containers on the default Wings network reach each other directly, so Bifrost-to-Quark WebRTC needs no extra
allocations for Quark.

### Keys

- `bifrost-proxy.key` lets anyone holding it join trusting backends as any player. Don't share it, and keep it
  out of backups you share (`.pteroignore` can exclude it from panel backups). Anyone with file access to the
  server, or the ability to upload plugins, can read it. If it leaks, delete it, restart, and replace the key in
  `trusted-proxy-keys`.
- Keep `bifrost-identity.der`. Losing it makes players confirm a new key.
- Don't switch to `auth = "off"` for production: logins can then be replayed. Bifrost refuses managed mode without
  `verify`.

### Limitations

- **Blocked on a nethernet-zig fix.** Docker 25+ blocks io_uring in its default seccomp profile, which Wings uses, so
  Bifrost's event loop falls back to epoll. nethernet-zig opens its Linux signaling socket without `SOCK_NONBLOCK`
  (`src/endpoint/listener.zig`), so `accept()` blocks the event loop: the port accepts connections but never
  answers, and signals are ignored. Until Bifrost pins a nethernet-zig with that flag, the installer's start check
  fails with `Bifrost did not start and stop cleanly`.
- Not yet run on a live Panel/Wings: real player joins through Docker NAT, STUN and `udp_mux`, and Bifrost-to-Quark
  over the Wings network. Upstream also lists no real Bedrock client join yet ([known issues](https://github.com/TrixNEW/Bifrost/blob/main/docs/known-issues.md)).
- ARM64 isn't supported.
