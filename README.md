# Hetzner Cloud Python Tools

A comprehensive Python-based toolkit for deploying and managing Hetzner Cloud servers with interactive features, multiple instance support, robust error handling, and comprehensive test coverage.

## 🐍 Python-First Approach

This toolkit is built entirely in Python for maximum reliability and cross-platform compatibility:

- **`deploy.py`** - Interactive server deployment tool with multi-instance support
- **`manage.py`** - Comprehensive server management tool with enhanced safety features

### Why Python?

- ✅ **Reliable interactive menus** - Perfect display of selection lists
- ✅ **Superior error handling** - Clear error messages and graceful failures  
- ✅ **JSON API integration** - Direct parsing of hcloud JSON output
- ✅ **Cross-platform compatibility** - Works on macOS, Linux, and Windows
- ✅ **Maintainable codebase** - Clean, readable, and extensible
- ✅ **No external dependencies** - Uses only Python standard library
- ✅ **Comprehensive test coverage** - 100% passing test suites for both tools

## 🚀 Features

### Deployment Tool (`deploy.py`)
- **Interactive Mode**: Guided deployment with selection menus for all options
- **Multiple Instance Deployment**: Deploy multiple identical servers with a single command
- **Smart Server Naming**: Automatic naming with zero-padded numbers (server-001, server-002, etc.) or individual custom names
- **Intelligent Configuration Flow**: Asks for server count first, then collects appropriate names
- **Location-First Selection**: Choose datacenter location before server type for better filtering
- **Region-Specific Filtering**: Only shows server types available in selected location
- **Volume Management**: Automatic volume creation and attachment per server
- **SSH Key Management**: Upload new keys or select from existing ones
- **Firewall & Network Support**: Attach firewalls and networks during deployment
- **Tag Support**: User-friendly tag format with automatic conversion
- **Cloud-Init Support**: Custom server initialization scripts
- **Dry-Run Mode**: Preview deployments without executing
- **Color-Coded Output**: Clear visual feedback throughout the process
- **Post-Deployment SSH Info**: Displays ready-to-use SSH connection commands after successful deployment
- **Smart User Detection**: Automatically determines SSH user based on OS image

### Management Tool (`manage.py`)
- **Server Operations**: Start, stop, restart, delete, resize servers
- **Server Information**: Detailed server info and status
- **SSH Access**: Direct SSH connection to servers
- **Interactive Server Deletion**: Enhanced delete command with server listing and selection
- **Enhanced Safety**: Requires typing "YES" (case-sensitive) for destructive operations
- **SSH Key Management**: Add, list, delete SSH keys with file validation
- **Volume Operations**: Create, attach, detach, delete volumes
- **Comprehensive Listing**: View all servers, keys, and volumes with formatted output
- **Error Handling**: Graceful handling of API failures and malformed responses

## 🧪 Test Coverage

Both tools include comprehensive test suites with **100% success rates**:

### Deploy Tool Tests (`tests/test_deploy.py`)
- **20 tests** covering all major functionality
- **100% success rate** - all tests passing
- Tests API interactions, utility functions, error handling, and business logic
- Realistic environment integration using actual `.env` configuration
- Comprehensive mocking to avoid side effects

### Management Tool Tests (`tests/test_manage.py`)
- **43 tests** covering all HetznerManager functionality  
- **100% success rate** - all tests passing
- Tests server operations, SSH key management, volume operations, and interactive flows
- Error handling scenarios including malformed JSON and API failures
- Interactive flow testing with user confirmation prompts

### Running Tests
```bash
# Run all tests
python3 run_tests.py

# Run specific test suite
python3 run_tests.py --deploy    # Deploy tool tests only
python3 run_tests.py --manage    # Management tool tests only

# Run individual test files
python3 tests/test_deploy.py
python3 tests/test_manage.py
```

## 📋 Prerequisites

1. **Hetzner Cloud CLI**: Install the official `hcloud` CLI tool
   ```bash
   # macOS
   brew install hcloud
   
   # Linux
   wget https://github.com/hetznercloud/cli/releases/latest/download/hcloud-linux-amd64.tar.gz
   tar -xzf hcloud-linux-amd64.tar.gz
   sudo mv hcloud /usr/local/bin/
   
   # Windows
   # Download from: https://github.com/hetznercloud/cli/releases
   ```

2. **Python 3.7+**: The tools use only Python standard library
   ```bash
   python3 --version  # Should be 3.7 or higher
   ```

3. **Hetzner Cloud API Token**: Get your token from the Hetzner Cloud Console

## ⚙️ Setup

1. **Clone or download** this repository
2. **Create environment file** from the example:
   ```bash
   cp .env.example .env
   ```
3. **Edit `.env`** with your configuration:
   ```bash
   # Required
   HETZNER_TOKEN=your_hetzner_cloud_api_token_here
   
   # Optional defaults for deployment
   DEFAULT_SERVER_TYPE=cpx21
   DEFAULT_IMAGE=ubuntu-24.04
   DEFAULT_LOCATION=nbg1
   DEFAULT_SSH_KEY_NAME=my-key

   # Optional defaults for volumes
   DEFAULT_VOLUME_SIZE=20

   # Optional network settings
   DEFAULT_FIREWALL=
   DEFAULT_NETWORK=
   ```

## 🎯 Quick Start

### Interactive Deployment
```bash
# Launch interactive mode - guided deployment experience
python3 deploy.py --interactive

# Interactive with multiple servers
python3 deploy.py --interactive -c 3
```

### Command Line Deployment
```bash
# Single server
python3 deploy.py -n my-server -s cpx21 -i ubuntu-24.04

# Multiple servers with base naming
python3 deploy.py -n web -c 3 -s cpx21 -i ubuntu-24.04
# Creates: web-001, web-002, web-003

# Server with volume and firewall
python3 deploy.py -n db-server -s cpx31 -i ubuntu-24.04 -v 50 -f web-firewall
```

### Server Management
```bash
# List all servers
python3 manage.py list

# Get detailed server information
python3 manage.py info server-name

# Server control
python3 manage.py start server-name
python3 manage.py stop server-name
python3 manage.py restart server-name

# Interactive server deletion (shows server list)
python3 manage.py delete

# Direct server deletion (with confirmation)
python3 manage.py delete server-name

# Delete server without confirmation (use with caution)
python3 manage.py delete server-name --yes

# SSH into server
python3 manage.py ssh server-name

# Resize server
python3 manage.py resize server-name cpx31
```

## 📖 Detailed Usage

### Deployment Tool (`deploy.py`)

#### Interactive Mode
The interactive mode provides a guided experience:
1. **Server Count**: Choose how many servers to deploy
2. **Server Names**: Individual names or base name for auto-numbering
3. **Image Selection**: Choose from available OS images (deduplicated system images only)
4. **Location Selection**: Choose datacenter location first
5. **Server Type**: Select from types available in chosen location
6. **SSH Key**: Upload new key or select existing
7. **Optional Features**: Volumes, firewalls, networks, cloud-init

#### Command Line Options
```bash
python3 deploy.py [OPTIONS]

Required (or use interactive mode):
  -n, --name TEXT           Server name (base name for multiple servers)
  -s, --server-type TEXT    Server type (e.g., cpx21, cpx31)
  -i, --image TEXT          OS image (e.g., ubuntu-24.04, debian-12)

Optional:
  -c, --count INTEGER       Number of servers to deploy (default: 1)
  -l, --location TEXT       Datacenter location (e.g., nbg1, fsn1, hel1)
  -k, --ssh-key TEXT        SSH key name or path to public key file
  -v, --volume INTEGER      Volume size in GB (creates and attaches volume)
  -f, --firewall TEXT       Firewall name to attach
  -w, --network TEXT        Network name to attach
  -t, --tags TEXT           Tags in format "key:value,key2:value2"
  --cloud-init TEXT         Path to cloud-init configuration file
  --interactive             Launch interactive mode
  --dry-run                 Preview deployment without executing
  --help                    Show help message
```

#### Examples
```bash
# Interactive deployment
python3 deploy.py --interactive

# Single server with all options
python3 deploy.py -n web-server -s cpx21 -i ubuntu-24.04 -l nbg1 -k my-key -v 20 -f web-firewall -t "env:prod,type:web"

# Multiple servers with base naming
python3 deploy.py -n api -c 5 -s cpx31 -i ubuntu-24.04 --interactive

# Dry run to preview
python3 deploy.py -n test-server -s cpx11 -i debian-12 --dry-run
```

### Management Tool (`manage.py`)

#### Server Management
```bash
# List all servers
python3 manage.py list

# Get detailed server information
python3 manage.py info server-name

# Server control
python3 manage.py start server-name
python3 manage.py stop server-name
python3 manage.py restart server-name

# Interactive server deletion (shows server list)
python3 manage.py delete

# Direct server deletion (with confirmation)
python3 manage.py delete server-name

# Delete server without confirmation (use with caution)
python3 manage.py delete server-name --yes

# SSH into server
python3 manage.py ssh server-name

# Resize server
python3 manage.py resize server-name cpx31
```

#### SSH Key Management
```bash
# List SSH keys
python3 manage.py list-keys

# Add SSH key from file
python3 manage.py add-key my-new-key ~/.ssh/id_rsa.pub

# Delete SSH key (with confirmation)
python3 manage.py delete-key key-name
```

#### Volume Management
```bash
# List volumes
python3 manage.py list-volumes

# Create volume
python3 manage.py create-volume my-volume 50

# Attach volume to server
python3 manage.py attach-volume my-volume server-name

# Detach volume from server
python3 manage.py detach-volume my-volume

# Delete volume (with confirmation)
python3 manage.py delete-volume my-volume
```

## 📁 Project Structure

```
hetzner-cli-wrapper/
├── deploy.py              # Main deployment tool
├── manage.py              # Server management tool
├── run_tests.py           # Test runner script
├── .env                   # Environment configuration (create from .env.example)
├── .env.example           # Environment template
├── README.md              # This documentation
├── requirements.txt       # Python dependencies (none required)
└── tests/                 # Test suite directory
    ├── __init__.py        # Python package marker
    ├── test_deploy.py     # Deploy tool tests (20 tests)
    └── test_manage.py     # Management tool tests (43 tests)
```

## 🔧 Configuration

The `.env` file supports the following configuration options:

```bash
# Required
HETZNER_TOKEN=your_hetzner_cloud_api_token_here

# Optional defaults for deployment
DEFAULT_SERVER_TYPE=cpx21
DEFAULT_IMAGE=ubuntu-24.04
DEFAULT_LOCATION=nbg1
DEFAULT_SSH_KEY_NAME=my-key

# Optional defaults for volumes
DEFAULT_VOLUME_SIZE=20

# Optional network settings
DEFAULT_FIREWALL=
DEFAULT_NETWORK=
```

## 🛡️ Security Best Practices

1. **Keep your API token secure** - Never commit `.env` to version control
2. **Use SSH keys** for server access instead of passwords
3. **Configure firewalls** to restrict access to necessary ports only
4. **Use private networks** for internal server communication
5. **Apply security updates** via cloud-init configuration
6. **Use tags** to organize and identify resources
7. **Review server configurations** before deployment using `--dry-run`
8. **Use confirmation prompts** for destructive operations (enabled by default)

## 🐛 Troubleshooting

### Common Issues

1. **"hcloud CLI not found"**
   - Install the Hetzner Cloud CLI tool
   - Ensure it's in your system PATH

2. **"Invalid API token"**
   - Check your `.env` file has the correct `HETZNER_TOKEN`
   - Verify the token in Hetzner Cloud Console

3. **"Server type not available in location"**
   - Use interactive mode to see available combinations
   - Check Hetzner Cloud documentation for availability

4. **"SSH key file not found"**
   - Verify the path to your SSH public key file
   - Use `~/.ssh/id_rsa.pub` for default SSH key location

5. **Tests failing**
   - Ensure `.env` file exists with valid `HETZNER_TOKEN`
   - Run individual test files to isolate issues
   - Check that `hcloud` CLI is installed and accessible

### Debug Mode

Both tools provide verbose output for troubleshooting:
```bash
# Enable debug output (if implemented)
python3 deploy.py --debug
python3 manage.py --debug
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Add tests** for new functionality
4. **Ensure all tests pass**: `python3 run_tests.py`
5. **Submit** a pull request

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add comprehensive tests for new features
- Update documentation for any changes
- Ensure backward compatibility
- Test on multiple platforms when possible

## 📄 License

This project is open source. Feel free to use, modify, and distribute according to your needs.

## 🙏 Acknowledgments

- **Hetzner Cloud** for providing excellent cloud infrastructure
- **Hetzner Cloud CLI** team for the robust `hcloud` tool
- **Python Community** for the excellent standard library

---

Code written by the fine folks at https://corrie.ai and https://highside.ai with the assistance of Windsurf AI and Claude 4 Sonnet.