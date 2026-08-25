# Quark Egg

A Pterodactyl egg for running [Quark](https://github.com/Bedrock-Phanatics/Quark), a high-performance Minecraft: Bedrock server software based on PocketMine-MP and Axolotl.

Quark is designed around performance, efficiency, and greater use of native C/C++ extensions while maintaining compatibility with the PocketMine-MP ecosystem where possible.

## Requirements

This egg is specifically built for:

* **Quark / PocketMine-MP 5**
* **PHP 8.4**
* **Linux x86_64**
* **Pterodactyl Panel**

Other PocketMine versions and PHP versions are not supported by this egg.

## PHP Runtime

The egg uses the custom PHP 8.4 PM5 binaries maintained by Bedrock-Phanatics:

[Bedrock-Phanatics/PHP-Binaries](https://github.com/Bedrock-Phanatics/PHP-Binaries)

Specifically:

```text
pm5-php-8.4-latest
```

## Installation

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

## Startup

Quark is started using:

```bash
./bin/php7/bin/php ./PocketMine-MP.phar --no-wizard
```

## Updating Quark

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

## Architecture Support

Currently, this egg supports:

```text
Linux x86_64
```

The installer will stop if an unsupported architecture is detected instead of attempting to use an incompatible PHP binary.

## Related Projects

### Quark

High-performance Minecraft: Bedrock server software leveraging PHP, C, and C++ to push PocketMine-MP to its limits.

https://github.com/Bedrock-Phanatics/Quark

### PHP Binaries

Custom PocketMine-MP PHP builds used by Quark.

https://github.com/Bedrock-Phanatics/PHP-Binaries

## Disclaimer

Quark is a fork of PocketMine-MP and Axolotl and is not affiliated with Mojang Studios or Microsoft.

Minecraft is a trademark of Microsoft Corporation.
