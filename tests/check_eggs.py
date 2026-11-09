import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib


root = Path(__file__).resolve().parents[1]
eggs = {path.stem: json.loads(path.read_text()) for path in root.glob("*-egg.json")}
for egg in eggs.values():
    json.loads(egg["config"]["files"])
    json.loads(egg["config"]["startup"])
    for script in (egg["scripts"]["installation"]["script"], egg["startup"]):
        script = re.sub(r"\{\{([A-Z_]+)\}\}", r"${\1}", script)
        subprocess.run(["bash", "-n"], input=script, text=True, check=True)
        subprocess.run(["shellcheck", "-S", "warning", "-s", "bash", "-"], input=script, text=True, check=True)


with tempfile.TemporaryDirectory() as temporary:
    server = Path(temporary)
    extensions = "bin/php7/lib/php/extensions/no-debug-zts-test"
    (server / extensions).mkdir(parents=True)
    (server / "bin/php7/bin").mkdir()
    ini = server / "bin/php7/bin/php.ini"
    script = eggs["quark-pterodactyl-egg"]["scripts"]["installation"]["script"]
    script = script.split('echo "Configuring PHP extension directory..."')[1]
    script = script.split('echo "Installing Composer..."')[0]
    script = 'fail() { exit 1; }; work="$PWD"\n' + script
    for contents in ("", 'extension_dir="old/path"\n'):
        ini.write_text(contents)
        subprocess.run(["bash", "-euc", script], cwd=server, check=True)
        assert ini.read_text() == f'extension_dir="${{QUARK_SERVER_ROOT:-/home/container}}/{extensions}"\n'
    if php := os.environ.get("QUARK_TEST_PHP"):
        build = server / ".quark-build"
        build.mkdir()
        env = {key: value for key, value in os.environ.items() if key != "QUARK_SERVER_ROOT"}
        for prefix in (str(server), "/home/container"):
            if prefix == str(server):
                env["QUARK_SERVER_ROOT"] = prefix
            else:
                env.pop("QUARK_SERVER_ROOT")
            output = subprocess.check_output(
                [php, "-c", str(ini), "-r", 'echo ini_get("extension_dir");'], cwd=build, env=env, text=True,
            )
            assert output == f"{prefix}/{extensions}", output


def install_bifrost(server, **env):
    script = eggs["bifrost-pterodactyl-egg"]["scripts"]["installation"]["script"]
    script = script.replace("server=/mnt/server", 'server="$TEST_SERVER"')
    script = script.replace("--kill-after=5s 40s", "--kill-after=0.2s 2s")
    script = script.replace("seq 60", "seq 20").replace("sleep 0.5", "sleep 0.05")
    mocks = r'''
apt-get() { :; }
minisign() { :; }
tar() { :; }
ldd() { :; }
zig() { if [ "$1" = version ]; then echo 0.17.0; fi; }
curl() {
    while [ "$1" != -o ]; do shift; done
    printf '{"keys":[]}' >"$2"
}
git() {
    if [ "$1" = init ]; then
        cp -R "$TEST_FIXTURE" "$3"
    elif [ "$3" = rev-parse ]; then
        printf '%040d\n' 1
    fi
}
mv() {
    if [ "$1" = "$work/stage" ] && [ "${FAIL_RENAME:-0}" = 1 ]; then return 1; fi
    command mv "$@"
}
'''
    script = script.replace("set -euo pipefail", "set -euo pipefail\n" + mocks, 1)
    result = subprocess.run(
        ["bash"], input=script, text=True, capture_output=True, timeout=8,
        env={**os.environ, "TEST_SERVER": str(server), "TEST_FIXTURE": str(fixture), **env},
    )
    assert not (server / ".bifrost-build").exists(), result.stdout + result.stderr
    return result


with tempfile.TemporaryDirectory() as temporary:
    base = Path(temporary)
    fixture = base / "fixture"
    for directory in ("tools", "config", "zig-out/bin", ".deps/native/lib"):
        (fixture / directory).mkdir(parents=True)
    (fixture / "tools/setup-native.sh").write_text("exit 0\n")
    (fixture / "config/bifrost.toml").write_text("upstream example\n")
    (fixture / ".deps/native/lib/libdatachannel.so").touch()
    binary = fixture / "zig-out/bin/bifrost"
    binary.write_text('''#!/usr/bin/env python3
import os
import signal
import time
if os.environ.get("STUBBORN") == "1":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
else:
    signal.signal(signal.SIGTERM, lambda *_: exit(0))
print("listening on 0.0.0.0", flush=True)
while True:
    time.sleep(0.01)
''')
    binary.chmod(0o755)
    server = base / "server"
    server.mkdir()
    for port in ("0", "65536", "99999", "019132", "00080", "abc"):
        result = install_bifrost(server, SERVER_PORT=port)
        assert result.returncode != 0 and "invalid SERVER_PORT" in result.stderr
    for backend in ("host:0", "host:65536", "host:00080"):
        result = install_bifrost(server, BACKEND_ADDRESS=backend)
        assert result.returncode != 0 and "BACKEND_ADDRESS" in result.stderr
    result = install_bifrost(server, SERVER_PORT="65535", BACKEND_ADDRESS="[::1]:65535")
    assert result.returncode == 0, result.stdout + result.stderr
    config = server / "config/bifrost.toml"
    parsed = tomllib.loads(config.read_text())
    assert parsed["nethernet"]["port_min"] == 65535
    assert parsed["backend"][0]["address"] == "[::1]:65535"
    config.write_text("custom configuration\n")
    previous = server / "bifrost/bin/bifrost"
    previous.write_text("previous build\n")
    for env in ({"STUBBORN": "1"}, {"FAIL_RENAME": "1"}):
        result = install_bifrost(server, **env)
        assert result.returncode != 0, result.stdout + result.stderr
        assert previous.read_text() == "previous build\n", result.stdout + result.stderr
        assert config.read_text() == "custom configuration\n"
    result = install_bifrost(server)
    assert result.returncode == 0, result.stdout + result.stderr
    assert config.read_text() == "custom configuration\n"
    assert not (server / "bifrost.old").exists()

print("Egg syntax and installer regression checks passed")
