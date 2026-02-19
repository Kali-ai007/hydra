# Hydra - Expandable Credential Testing Tool

A plugin-based credential testing tool built in Python. Add new protocols by dropping a plugin file in plugins/. Includes a web dashboard for non-CLI users.

> For authorized security testing only. Only use against systems you own or have written permission to test.

## Features

- **Plugin architecture** - Add new protocols without touching core code
- **Auto-discovery** - Drop a plugin in plugins/ and it is instantly available
- **JSON pipeline** - Pipe targets from other tools (nmap, naabu, etc.)
- **Web dashboard** - Visual interface for launching scans and viewing results
- **Threaded** - Test multiple credentials in parallel
- **JSON output** - Structured results for reporting

## Supported Protocols

| Plugin | Name | Default Port |
|--------|------|-------------|
| HTTP Basic Auth | http-basic | 80 |
| SSH | ssh | 22 |
| FTP | ftp | 21 |

## Installation

    git clone https://github.com/Kali-ai007/hydra.git
    cd hydra
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Usage

### CLI Mode

    python hydra.py --list-plugins
    python hydra.py -t 192.168.1.100 -p http-basic -u admin -w wordlists/common.txt
    python hydra.py -t 192.168.1.100 -p ssh -u root -w wordlists/common.txt
    python hydra.py -t 192.168.1.100 -p ftp -u anonymous -P anonymous

### JSON Pipeline Mode

    echo '{"host":"192.168.1.1","port":22,"protocol":"ssh"}' | python hydra.py --pipe -u admin -w wordlists/common.txt
    cat targets.json | python hydra.py --pipe -u admin -w wordlists/common.txt

### Web Dashboard

    python hydra.py --dashboard
    # Open http://127.0.0.1:5000 in your browser

## Adding a New Plugin

Create a new file in plugins/ - the tool discovers it automatically:

    # plugins/my_protocol.py
    from plugins.base import PluginBase

    class MyProtocolPlugin(PluginBase):
        name = "my-protocol"
        default_port = 1234

        def attempt(self, host, port, username, password):
            # Your auth logic here
            return False

## Project Structure

    hydra/
    ├── hydra.py              <- CLI entry point
    ├── core/
    │   ├── engine.py         <- Attack engine with threading
    │   └── result.py         <- Result storage and JSON export
    ├── plugins/
    │   ├── base.py           <- Plugin blueprint (ABC)
    │   ├── http_basic.py     <- HTTP Basic Auth plugin
    │   ├── ssh.py            <- SSH plugin (paramiko)
    │   └── ftp.py            <- FTP plugin (built-in ftplib)
    ├── dashboard/
    │   └── app.py            <- Flask web dashboard
    ├── utils/
    │   └── logger.py         <- Colored terminal output
    ├── wordlists/
    │   └── common.txt        <- Default password list
    └── requirements.txt

## License

MIT
