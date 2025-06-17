#!/usr/bin/env python3
"""
Hetzner Cloud Server Management Tool
A Python wrapper for managing Hetzner Cloud resources
"""

import os
import sys
import subprocess
import argparse
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Color codes for terminal output
class Colors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

class HetznerManager:
    def __init__(self):
        self.config = {}
        self.load_env_config()
        
    def load_env_config(self):
        """Load configuration from .env file"""
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key] = value
            print(f"{Colors.GREEN}✓{Colors.NC} Loaded configuration from .env")
        
    def run_hcloud_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """Run hcloud command with proper token setup"""
        env = os.environ.copy()
        if 'HETZNER_TOKEN' in self.config:
            env['HCLOUD_TOKEN'] = self.config['HETZNER_TOKEN']
        
        try:
            result = subprocess.run(
                ['hcloud'] + cmd,
                capture_output=True,
                text=True,
                env=env
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, str(e)
        except FileNotFoundError:
            return False, "hcloud CLI not found"
    
    def check_dependencies(self) -> bool:
        """Check if hcloud CLI is available"""
        success, _ = self.run_hcloud_command(['version'])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} hcloud CLI is available")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} hcloud CLI not found. Please install it first.")
            return False
    
    def validate_token(self) -> bool:
        """Validate Hetzner Cloud API token"""
        if 'HETZNER_TOKEN' not in self.config or not self.config['HETZNER_TOKEN']:
            print(f"{Colors.RED}✗{Colors.NC} Hetzner Cloud API token is required")
            print("Set HETZNER_TOKEN in .env file")
            return False
        
        success, _ = self.run_hcloud_command(['context', 'list'])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} API token is valid")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Invalid Hetzner Cloud API token")
            return False

    # Server Management Functions
    def list_servers(self) -> bool:
        """List all servers"""
        print(f"{Colors.BLUE}Listing servers...{Colors.NC}")
        success, output = self.run_hcloud_command(['server', 'list'])
        if success:
            print(output)
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to list servers: {output}")
            return False
    
    def server_info(self, server_name: str) -> bool:
        """Show detailed server information"""
        print(f"{Colors.BLUE}Getting server info for: {server_name}{Colors.NC}")
        success, output = self.run_hcloud_command(['server', 'describe', server_name])
        if success:
            print(output)
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to get server info: {output}")
            return False
    
    def start_server(self, server_name: str) -> bool:
        """Start a server"""
        print(f"{Colors.YELLOW}→{Colors.NC} Starting server: {server_name}")
        success, output = self.run_hcloud_command(['server', 'poweron', server_name])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Server started successfully: {server_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to start server: {output}")
            return False
    
    def stop_server(self, server_name: str) -> bool:
        """Stop a server"""
        print(f"{Colors.YELLOW}→{Colors.NC} Stopping server: {server_name}")
        success, output = self.run_hcloud_command(['server', 'poweroff', server_name])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Server stopped successfully: {server_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to stop server: {output}")
            return False
    
    def restart_server(self, server_name: str) -> bool:
        """Restart a server"""
        print(f"{Colors.YELLOW}→{Colors.NC} Restarting server: {server_name}")
        success, output = self.run_hcloud_command(['server', 'reboot', server_name])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Server restarted successfully: {server_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to restart server: {output}")
            return False
    
    def delete_server(self, server_name: str, confirm: bool = False) -> bool:
        """Delete a server"""
        if not confirm:
            # Show server details before deletion
            print(f"{Colors.BLUE}Server to be deleted:{Colors.NC}")
            success, output = self.run_hcloud_command(['server', 'describe', server_name])
            if success:
                print(output)
            else:
                print(f"{Colors.RED}Warning: Could not retrieve server details{Colors.NC}")
            
            print(f"\n{Colors.RED}⚠️  WARNING: This action cannot be undone!{Colors.NC}")
            response = input(f"Type 'YES' to confirm deletion of server '{server_name}': ")
            if response != 'YES':
                print("Operation cancelled (must type exactly 'YES' to confirm)")
                return False
        
        print(f"{Colors.YELLOW}→{Colors.NC} Deleting server: {server_name}")
        success, output = self.run_hcloud_command(['server', 'delete', server_name])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Server deleted successfully: {server_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to delete server: {output}")
            return False
    
    def interactive_delete(self) -> bool:
        """Interactive server deletion with server selection"""
        print(f"{Colors.BLUE}Available servers for deletion:{Colors.NC}")
        servers = self.get_servers()
        if not servers:
            print(f"{Colors.YELLOW}No servers found{Colors.NC}")
            return True
        
        # Display servers with numbers
        for i, server in enumerate(servers, 1):
            print(f"  {i}. {server}")
        
        try:
            choice = input(f"\nSelect server to delete (1-{len(servers)}) or 0 to cancel: ")
            if choice == '0':
                print("Operation cancelled")
                return True
            
            server_index = int(choice) - 1
            if 0 <= server_index < len(servers):
                selected_server = servers[server_index]
                return self.delete_server(selected_server, confirm=False)
            else:
                print(f"{Colors.RED}Invalid selection{Colors.NC}")
                return False
        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled")
            return False
    
    def get_servers(self) -> List[str]:
        """Get list of server names"""
        success, output = self.run_hcloud_command(['server', 'list', '-o', 'json'])
        if success:
            try:
                data = json.loads(output)
                return [server['name'] for server in data]
            except json.JSONDecodeError:
                return []
        return []
    
    def ssh_server(self, server_name: str) -> bool:
        """SSH into a server"""
        print(f"{Colors.BLUE}Getting IP for server: {server_name}{Colors.NC}")
        success, output = self.run_hcloud_command(['server', 'ip', server_name])
        if success:
            ip = output.strip()
            print(f"{Colors.YELLOW}→{Colors.NC} Connecting to {server_name} ({ip})")
            os.system(f"ssh root@{ip}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to get server IP: {output}")
            return False
    
    def resize_server(self, server_name: str, server_type: str) -> bool:
        """Resize server to new type"""
        print(f"{Colors.YELLOW}→{Colors.NC} Resizing server {server_name} to {server_type}")
        success, output = self.run_hcloud_command(['server', 'change-type', server_name, server_type])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Server resized successfully: {server_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to resize server: {output}")
            return False

    # SSH Key Management Functions
    def list_ssh_keys(self) -> bool:
        """List all SSH keys"""
        print(f"{Colors.BLUE}Listing SSH keys...{Colors.NC}")
        success, output = self.run_hcloud_command(['ssh-key', 'list'])
        if success:
            print(output)
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to list SSH keys: {output}")
            return False
    
    def add_ssh_key(self, key_name: str, key_file: str) -> bool:
        """Add SSH key from file"""
        if not os.path.exists(key_file):
            print(f"{Colors.RED}✗{Colors.NC} SSH key file not found: {key_file}")
            return False
        
        print(f"{Colors.YELLOW}→{Colors.NC} Adding SSH key: {key_name}")
        success, output = self.run_hcloud_command(['ssh-key', 'create', '--name', key_name, '--public-key-from-file', key_file])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} SSH key added successfully: {key_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to add SSH key: {output}")
            return False
    
    def delete_ssh_key(self, key_name: str, confirm: bool = False) -> bool:
        """Delete SSH key"""
        if not confirm:
            response = input(f"Are you sure you want to delete SSH key '{key_name}'? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Operation cancelled")
                return False
        
        print(f"{Colors.YELLOW}→{Colors.NC} Deleting SSH key: {key_name}")
        success, output = self.run_hcloud_command(['ssh-key', 'delete', key_name])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} SSH key deleted successfully: {key_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to delete SSH key: {output}")
            return False

    # Volume Management Functions
    def list_volumes(self) -> bool:
        """List all volumes"""
        print(f"{Colors.BLUE}Listing volumes...{Colors.NC}")
        success, output = self.run_hcloud_command(['volume', 'list'])
        if success:
            print(output)
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to list volumes: {output}")
            return False
    
    def create_volume(self, volume_name: str, size: int, location: str = 'nbg1') -> bool:
        """Create a volume"""
        print(f"{Colors.YELLOW}→{Colors.NC} Creating volume: {volume_name} ({size}GB)")
        success, output = self.run_hcloud_command([
            'volume', 'create',
            '--name', volume_name,
            '--size', str(size),
            '--location', location,
            '--format', 'ext4'
        ])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Volume created successfully: {volume_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to create volume: {output}")
            return False
    
    def attach_volume(self, server_name: str, volume_name: str) -> bool:
        """Attach volume to server"""
        print(f"{Colors.YELLOW}→{Colors.NC} Attaching volume {volume_name} to server {server_name}")
        success, output = self.run_hcloud_command(['volume', 'attach', volume_name, server_name])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Volume attached successfully")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to attach volume: {output}")
            return False
    
    def detach_volume(self, volume_name: str) -> bool:
        """Detach volume from server"""
        print(f"{Colors.YELLOW}→{Colors.NC} Detaching volume: {volume_name}")
        success, output = self.run_hcloud_command(['volume', 'detach', volume_name])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Volume detached successfully: {volume_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to detach volume: {output}")
            return False
    
    def delete_volume(self, volume_name: str, confirm: bool = False) -> bool:
        """Delete a volume"""
        if not confirm:
            response = input(f"Are you sure you want to delete volume '{volume_name}'? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Operation cancelled")
                return False
        
        print(f"{Colors.YELLOW}→{Colors.NC} Deleting volume: {volume_name}")
        success, output = self.run_hcloud_command(['volume', 'delete', volume_name])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Volume deleted successfully: {volume_name}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to delete volume: {output}")
            return False

def main():
    """Main function to handle command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Hetzner Cloud Server Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 manage.py list                    # List all servers
  python3 manage.py info my-server         # Show server details
  python3 manage.py start my-server        # Start a server
  python3 manage.py stop my-server         # Stop a server
  python3 manage.py delete my-server       # Delete a server
  python3 manage.py ssh my-server          # SSH into server
  python3 manage.py resize my-server cpx21 # Resize server
  
  python3 manage.py list-keys              # List SSH keys
  python3 manage.py add-key mykey ~/.ssh/id_rsa.pub
  python3 manage.py delete-key mykey       # Delete SSH key
  
  python3 manage.py list-volumes           # List volumes
  python3 manage.py create-volume myvolume 10
  python3 manage.py attach-volume my-server myvolume
  python3 manage.py detach-volume myvolume
  python3 manage.py delete-volume myvolume
        """
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server commands
    subparsers.add_parser('list', help='List all servers')
    
    info_parser = subparsers.add_parser('info', help='Show server information')
    info_parser.add_argument('server_name', help='Server name')
    
    start_parser = subparsers.add_parser('start', help='Start a server')
    start_parser.add_argument('server_name', help='Server name')
    
    stop_parser = subparsers.add_parser('stop', help='Stop a server')
    stop_parser.add_argument('server_name', help='Server name')
    
    restart_parser = subparsers.add_parser('restart', help='Restart a server')
    restart_parser.add_argument('server_name', help='Server name')
    
    delete_parser = subparsers.add_parser('delete', help='Delete a server')
    delete_parser.add_argument('server_name', nargs='?', help='Server name (optional - will list servers if not provided)')
    delete_parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    
    ssh_parser = subparsers.add_parser('ssh', help='SSH into a server')
    ssh_parser.add_argument('server_name', help='Server name')
    
    resize_parser = subparsers.add_parser('resize', help='Resize a server')
    resize_parser.add_argument('server_name', help='Server name')
    resize_parser.add_argument('server_type', help='New server type')
    
    # SSH Key commands
    subparsers.add_parser('list-keys', help='List SSH keys')
    
    add_key_parser = subparsers.add_parser('add-key', help='Add SSH key')
    add_key_parser.add_argument('key_name', help='SSH key name')
    add_key_parser.add_argument('key_file', help='Path to public key file')
    
    delete_key_parser = subparsers.add_parser('delete-key', help='Delete SSH key')
    delete_key_parser.add_argument('key_name', help='SSH key name')
    delete_key_parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    
    # Volume commands
    subparsers.add_parser('list-volumes', help='List volumes')
    
    create_vol_parser = subparsers.add_parser('create-volume', help='Create volume')
    create_vol_parser.add_argument('volume_name', help='Volume name')
    create_vol_parser.add_argument('size', type=int, help='Volume size in GB')
    create_vol_parser.add_argument('--location', default='nbg1', help='Volume location')
    
    attach_vol_parser = subparsers.add_parser('attach-volume', help='Attach volume to server')
    attach_vol_parser.add_argument('server_name', help='Server name')
    attach_vol_parser.add_argument('volume_name', help='Volume name')
    
    detach_vol_parser = subparsers.add_parser('detach-volume', help='Detach volume')
    detach_vol_parser.add_argument('volume_name', help='Volume name')
    
    delete_vol_parser = subparsers.add_parser('delete-volume', help='Delete volume')
    delete_vol_parser.add_argument('volume_name', help='Volume name')
    delete_vol_parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize manager
    manager = HetznerManager()
    
    # Check dependencies
    if not manager.check_dependencies():
        return 1
    
    # Validate token
    if not manager.validate_token():
        return 1
    
    # Execute commands
    try:
        if args.command == 'list':
            success = manager.list_servers()
        elif args.command == 'info':
            success = manager.server_info(args.server_name)
        elif args.command == 'start':
            success = manager.start_server(args.server_name)
        elif args.command == 'stop':
            success = manager.stop_server(args.server_name)
        elif args.command == 'restart':
            success = manager.restart_server(args.server_name)
        elif args.command == 'delete':
            if args.server_name:
                success = manager.delete_server(args.server_name, args.yes)
            else:
                success = manager.interactive_delete()
        elif args.command == 'ssh':
            success = manager.ssh_server(args.server_name)
        elif args.command == 'resize':
            success = manager.resize_server(args.server_name, args.server_type)
        elif args.command == 'list-keys':
            success = manager.list_ssh_keys()
        elif args.command == 'add-key':
            success = manager.add_ssh_key(args.key_name, args.key_file)
        elif args.command == 'delete-key':
            success = manager.delete_ssh_key(args.key_name, args.yes)
        elif args.command == 'list-volumes':
            success = manager.list_volumes()
        elif args.command == 'create-volume':
            success = manager.create_volume(args.volume_name, args.size, args.location)
        elif args.command == 'attach-volume':
            success = manager.attach_volume(args.server_name, args.volume_name)
        elif args.command == 'detach-volume':
            success = manager.detach_volume(args.volume_name)
        elif args.command == 'delete-volume':
            success = manager.delete_volume(args.volume_name, args.yes)
        else:
            print(f"{Colors.RED}✗{Colors.NC} Unknown command: {args.command}")
            return 1
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.NC}")
        return 1
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.NC} Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
