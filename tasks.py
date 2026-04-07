"""Invoke tasks for Akita-Zmodem-MeshCore.

Usage:
    inv send --dest <node_id> --path <file_or_dir>
    inv receive --path <save_path> [--overwrite] [--directory]
    inv listen --dir <save_dir>
    inv status
    inv config [--show]
    inv checksum --path <file>
    inv test [--verbose]
    inv lint
"""

import os
import sys

from invoke import task

PYTHON = sys.executable
SCRIPT = "akita_zmodem_meshcore.py"
CONFIG_FILE = "akita_zmodem_meshcore_config.json"


def _base_args(c, config=None, debug=False, mesh_type=None,
               serial_port=None, serial_baud=None,
               tcp_host=None, tcp_port=None):
    """Build the common CLI prefix."""
    parts = [PYTHON, SCRIPT]
    if config:
        parts += ["--config", config]
    if debug:
        parts.append("--debug")
    if mesh_type:
        parts += ["--mesh-type", mesh_type]
    if serial_port:
        parts += ["--serial-port", serial_port]
    if serial_baud:
        parts += ["--serial-baud", str(serial_baud)]
    if tcp_host:
        parts += ["--tcp-host", tcp_host]
    if tcp_port:
        parts += ["--tcp-port", str(tcp_port)]
    return parts


# ---------------------------------------------------------------------------
# Core transfer tasks
# ---------------------------------------------------------------------------

@task(
    help={
        "dest": "Destination node ID (64-char hex pubkey)",
        "path": "File or directory to send",
        "route": "Outbound route as hex repeater hashes (e.g. '5f3a') or 'flood'",
        "debug": "Enable debug logging",
        "config": "Path to config JSON file",
        "mesh-type": "Connection type: serial or tcp",
        "serial-port": "Serial device path",
        "serial-baud": "Serial baud rate",
        "tcp-host": "TCP host",
        "tcp-port": "TCP port",
    }
)
def send(c, dest, path, route=None, debug=False, config=None, mesh_type=None,
         serial_port=None, serial_baud=None, tcp_host=None, tcp_port=None):
    """Send a file or directory to a mesh node."""
    parts = _base_args(c, config, debug, mesh_type,
                       serial_port, serial_baud, tcp_host, tcp_port)
    parts += ["send", dest, path]
    if route:
        parts += ["--route", route]
    c.run(" ".join(f'"{p}"' if " " in p else p for p in parts), pty=False)


@task(
    help={
        "path": "Save path (file or directory)",
        "overwrite": "Overwrite existing files",
        "directory": "Force treat path as directory",
        "debug": "Enable debug logging",
        "config": "Path to config JSON file",
        "mesh-type": "Connection type: serial or tcp",
        "serial-port": "Serial device path",
        "serial-baud": "Serial baud rate",
        "tcp-host": "TCP host",
        "tcp-port": "TCP port",
    }
)
def receive(c, path, overwrite=False, directory=False, debug=False,
            config=None, mesh_type=None,
            serial_port=None, serial_baud=None, tcp_host=None, tcp_port=None):
    """Receive a single file or directory from the mesh."""
    parts = _base_args(c, config, debug, mesh_type,
                       serial_port, serial_baud, tcp_host, tcp_port)
    parts += ["receive", path]
    if overwrite:
        parts.append("--overwrite")
    if directory:
        parts.append("--directory")
    c.run(" ".join(f'"{p}"' if " " in p else p for p in parts), pty=False)


@task(
    help={
        "dir": "Directory to save received files into",
        "no-overwrite": "Skip files that already exist instead of overwriting",
        "debug": "Enable debug logging",
        "config": "Path to config JSON file",
        "mesh-type": "Connection type: serial or tcp",
        "serial-port": "Serial device path",
        "serial-baud": "Serial baud rate",
        "tcp-host": "TCP host",
        "tcp-port": "TCP port",
    }
)
def listen(c, dir, no_overwrite=False, debug=False, config=None, mesh_type=None,
           serial_port=None, serial_baud=None, tcp_host=None, tcp_port=None):
    """Listen for incoming files and save them to a directory."""
    parts = _base_args(c, config, debug, mesh_type,
                       serial_port, serial_baud, tcp_host, tcp_port)
    parts += ["listen", dir]
    if no_overwrite:
        parts.append("--no-overwrite")
    c.run(" ".join(f'"{p}"' if " " in p else p for p in parts), pty=False)


# ---------------------------------------------------------------------------
# Utility tasks
# ---------------------------------------------------------------------------

@task(help={"show": "Print the current configuration to stdout"})
def config(c, show=False):
    """Show or create the default configuration file."""
    if show:
        if os.path.exists(CONFIG_FILE):
            c.run(f'{PYTHON} -m json.tool "{CONFIG_FILE}"')
        else:
            print(f"Config file '{CONFIG_FILE}' not found; creating with defaults.")
            c.run(f'{PYTHON} -c "'
                  f"from akita_zmodem_meshcore import load_config; load_config()"
                  f'"')
            c.run(f'{PYTHON} -m json.tool "{CONFIG_FILE}"')
    else:
        print(f"Config file: {os.path.abspath(CONFIG_FILE)}")
        if os.path.exists(CONFIG_FILE):
            print("  (exists)")
        else:
            print("  (will be created on first run)")


@task(help={"path": "File to compute MD5 checksum for"})
def checksum(c, path):
    """Compute the MD5 checksum of a file (for transfer verification)."""
    c.run(f'{PYTHON} -c "'
          f"from akita_zmodem_meshcore import calculate_md5; "
          f"print(calculate_md5(r\\'{path}\\'))"
          f'"')


@task(help={"id": "Transfer ID to query"})
def status(c, id=None):
    """Print transfer status (requires a running daemon)."""
    if id is not None:
        print(f"Transfer #{id} — status query requires a running daemon instance.")
    else:
        print("No running daemon to query. Start one with `inv listen --dir <dir>`.")


@task(help={"id": "Transfer ID to cancel"})
def cancel(c, id):
    """Cancel a transfer (requires a running daemon)."""
    print(f"Transfer #{id} — cancel requires a running daemon instance.")


@task(
    help={
        "verbose": "Show verbose test output",
        "k": "Only run tests matching this expression (pytest -k)",
    }
)
def test(c, verbose=False, k=None):
    """Run the test suite with pytest."""
    cmd = f"{PYTHON} -m pytest tests/"
    if verbose:
        cmd += " -v"
    if k:
        cmd += f" -k {k}"
    c.run(cmd, pty=False)


@task
def lint(c):
    """Run ruff linter/formatter on the project."""
    c.run(f"{PYTHON} -m ruff check akita_zmodem_meshcore.py zmodem.py tasks.py tests/",
          warn=True, pty=False)


@task(help={"fix": "Apply fixes automatically"})
def fmt(c, fix=False):
    """Format code with ruff."""
    cmd = f"{PYTHON} -m ruff format akita_zmodem_meshcore.py zmodem.py tasks.py tests/"
    if not fix:
        cmd += " --check"
    c.run(cmd, warn=True, pty=False)


@task(
    help={
        "config": "Path to config JSON file",
        "mesh-type": "Connection type: serial or tcp",
        "serial-port": "Serial device path",
        "serial-baud": "Serial baud rate",
        "tcp-host": "TCP host",
        "tcp-port": "TCP port",
    }
)
def contacts(c, config=None, mesh_type=None,
             serial_port=None, serial_baud=None,
             tcp_host=None, tcp_port=None):
    """Fetch and display the contact list from the connected mesh device."""
    parts = _base_args(c, config, False, mesh_type,
                       serial_port, serial_baud, tcp_host, tcp_port)
    parts.append("contacts")
    c.run(" ".join(f'"{p}"' if " " in p else p for p in parts), pty=False)


@task(
    help={
        "dest": "Destination node ID (64-char hex pubkey or prefix)",
        "route": "Route: hex repeater hashes (e.g. '5f3a'), 'direct', or 'flood'",
        "config": "Path to config JSON file",
        "mesh-type": "Connection type: serial or tcp",
        "serial-port": "Serial device path",
        "serial-baud": "Serial baud rate",
        "tcp-host": "TCP host",
        "tcp-port": "TCP port",
    }
)
def route(c, dest, route, config=None, mesh_type=None,
          serial_port=None, serial_baud=None,
          tcp_host=None, tcp_port=None):
    """Set the outbound route for a contact (direct, flood, or hex path)."""
    parts = _base_args(c, config, False, mesh_type,
                       serial_port, serial_baud, tcp_host, tcp_port)
    parts += ["route", dest, route]
    c.run(" ".join(f'"{p}"' if " " in p else p for p in parts), pty=False)


@task
def deps(c):
    """Install all dependencies (runtime + dev)."""
    c.run(f"{PYTHON} -m pip install -r requirements.txt -r requirements-dev.txt")


@task
def clean(c):
    """Remove temporary and build artifacts."""
    import shutil
    patterns = ["__pycache__", ".pytest_cache", "*.pyc", "*.pyo"]
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d in ("__pycache__", ".pytest_cache"):
                path = os.path.join(root, d)
                print(f"Removing {path}")
                shutil.rmtree(path, ignore_errors=True)
        for f in files:
            if f.endswith((".pyc", ".pyo")):
                path = os.path.join(root, f)
                print(f"Removing {path}")
                os.remove(path)
