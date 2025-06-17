#!/usr/bin/env python3
"""
Hetzner Cloud Server Deployment Tool
A Python wrapper for the Hetzner Cloud CLI with interactive features
"""

import os
import sys
import subprocess
import argparse
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import time

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

class HetznerDeployer:
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
            print("Set HETZNER_TOKEN in .env file or use --token option")
            return False
        
        success, _ = self.run_hcloud_command(['context', 'list'])
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} API token is valid")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Invalid Hetzner Cloud API token")
            return False
    
    def get_server_types(self, location: str = None) -> List[str]:
        """Get available server types, optionally filtered by location"""
        success, output = self.run_hcloud_command(['server-type', 'list', '-o', 'json'])
        if success:
            data = json.loads(output)
            server_types = []
            for item in data:
                # If location is specified, check if server type is available in that location
                if location:
                    # Get available locations for this server type
                    available_locations = [loc['location'] for loc in item.get('prices', [])]
                    if location in available_locations:
                        server_types.append(item['name'])
                else:
                    server_types.append(item['name'])
            return server_types
        return []
    
    def get_images(self) -> List[str]:
        """Get available images"""
        success, output = self.run_hcloud_command(['image', 'list', '-o', 'json'])
        if success:
            data = json.loads(output)
            # Filter for system images only (not user snapshots) and deduplicate
            images = set()  # Use set to automatically deduplicate
            for item in data:
                # Only include system images (type: 'system'), not user snapshots
                if item.get('type') == 'system':
                    name = item['name']
                    if any(os_name in name.lower() for os_name in 
                          ['ubuntu', 'debian', 'centos', 'almalinux', 'rocky', 'fedora', 'opensuse']):
                        images.add(name)
            return sorted(list(images))  # Convert back to sorted list
        return []
    
    def get_locations(self) -> List[str]:
        """Get available locations"""
        success, output = self.run_hcloud_command(['location', 'list', '-o', 'json'])
        if success:
            data = json.loads(output)
            return [item['name'] for item in data]
        return []
    
    def get_ssh_keys(self) -> List[str]:
        """Get available SSH keys"""
        success, output = self.run_hcloud_command(['ssh-key', 'list', '-o', 'json'])
        if success:
            data = json.loads(output)
            return [item['name'] for item in data]
        return []
    
    def get_firewalls(self) -> List[str]:
        """Get available firewalls"""
        success, output = self.run_hcloud_command(['firewall', 'list', '-o', 'json'])
        if success:
            data = json.loads(output)
            return [item['name'] for item in data]
        return []
    
    def get_networks(self) -> List[str]:
        """Get available networks"""
        success, output = self.run_hcloud_command(['network', 'list', '-o', 'json'])
        if success:
            data = json.loads(output)
            return [item['name'] for item in data]
        return []
    
    def select_from_list(self, prompt: str, options: List[str], allow_none: bool = False) -> Optional[str]:
        """Interactive selection from a list of options"""
        if not options:
            print(f"{Colors.RED}No options available{Colors.NC}")
            return None
        
        print(f"\n{Colors.CYAN}{prompt}{Colors.NC}")
        
        if allow_none:
            print("  0. None")
        
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        
        while True:
            try:
                max_choice = len(options) + (1 if allow_none else 0)
                choice = input(f"\nSelect option (0-{max_choice} or 1-{len(options)}): ").strip()
                
                if not choice:
                    continue
                    
                choice_num = int(choice)
                
                if allow_none and choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(options):
                    return options[choice_num - 1]
                else:
                    print(f"{Colors.RED}Invalid selection. Please choose 1-{len(options)}{Colors.NC}")
            except ValueError:
                print(f"{Colors.RED}Please enter a valid number{Colors.NC}")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled{Colors.NC}")
                sys.exit(0)
    
    def interactive_config(self, args) -> Dict:
        """Interactive configuration for missing values"""
        config = {}
        
        print(f"{Colors.BLUE}Interactive Configuration{Colors.NC}")
        print("=" * 25)
        
        # Server count first (when no name provided)
        if not args.name:
            while True:
                try:
                    count_input = input("How many servers to deploy? (default: 1): ").strip()
                    if not count_input:
                        config['count'] = 1
                        break
                    count = int(count_input)
                    if count > 0:
                        config['count'] = count
                        break
                    else:
                        print(f"{Colors.RED}Count must be greater than 0{Colors.NC}")
                except ValueError:
                    print(f"{Colors.RED}Please enter a valid number{Colors.NC}")
        else:
            config['count'] = args.count or 1
        
        # Server name(s) based on count
        if not args.name:
            if config['count'] == 1:
                # Single server - ask for one name
                while True:
                    name = input("Enter server name: ").strip()
                    if name:
                        config['name'] = name
                        config['server_names'] = [name]
                        break
                    print(f"{Colors.RED}Server name is required{Colors.NC}")
            else:
                # Multiple servers - ask for base name or individual names
                print(f"\n{Colors.BLUE}Server Naming Options:{Colors.NC}")
                print("1. Use base name (servers will be named: base-001, base-002, etc.)")
                print("2. Enter individual names for each server")
                
                while True:
                    choice = input("Choose option (1 or 2): ").strip()
                    if choice == '1':
                        # Base name approach
                        while True:
                            base_name = input("Enter base server name: ").strip()
                            if base_name:
                                config['name'] = base_name
                                config['server_names'] = [f"{base_name}-{i:03d}" for i in range(1, config['count'] + 1)]
                                break
                            print(f"{Colors.RED}Base name is required{Colors.NC}")
                        break
                    elif choice == '2':
                        # Individual names approach
                        server_names = []
                        print(f"\nEnter names for {config['count']} servers:")
                        for i in range(config['count']):
                            while True:
                                name = input(f"Server {i+1} name: ").strip()
                                if name:
                                    server_names.append(name)
                                    break
                                print(f"{Colors.RED}Server name is required{Colors.NC}")
                        config['name'] = server_names[0]  # Use first name as base
                        config['server_names'] = server_names
                        break
                    else:
                        print(f"{Colors.RED}Please enter 1 or 2{Colors.NC}")
        else:
            config['name'] = args.name
            if config['count'] == 1:
                config['server_names'] = [args.name]
            else:
                config['server_names'] = [f"{args.name}-{i:03d}" for i in range(1, config['count'] + 1)]
        
        # Image selection
        if not args.image:
            print(f"{Colors.YELLOW}→{Colors.NC} Fetching available images...")
            images = self.get_images()
            if images:
                config['image'] = self.select_from_list("Select image:", images)
            else:
                print(f"{Colors.RED}No images found{Colors.NC}")
                return None
        else:
            config['image'] = args.image
        
        # Location
        if not args.location:
            location = self.config.get('DEFAULT_LOCATION', 'nbg1')
            if args.interactive:
                print(f"{Colors.YELLOW}→{Colors.NC} Fetching available locations...")
                locations = self.get_locations()
                if locations:
                    selected = self.select_from_list(f"Select location (current: {location}):", locations)
                    config['location'] = selected or location
                else:
                    config['location'] = location
            else:
                config['location'] = location
        else:
            config['location'] = args.location
        
        # Server type
        if not args.server_type:
            server_type = self.config.get('DEFAULT_SERVER_TYPE', 'cpx11')
            if args.interactive:
                print(f"{Colors.YELLOW}→{Colors.NC} Fetching available server types for {config['location']}...")
                types = self.get_server_types(config['location'])
                if types:
                    selected = self.select_from_list(f"Select server type (current: {server_type}):", types)
                    config['server_type'] = selected or server_type
                else:
                    config['server_type'] = server_type
            else:
                config['server_type'] = server_type
        else:
            config['server_type'] = args.server_type
        
        # SSH Key
        if not args.ssh_key:
            ssh_key = self.config.get('DEFAULT_SSH_KEY_NAME', '')
            if args.interactive:
                print(f"{Colors.YELLOW}→{Colors.NC} Fetching available SSH keys...")
                keys = self.get_ssh_keys()
                if keys:
                    keys.append("Upload new SSH key")
                    selected = self.select_from_list("Select SSH key:", keys)
                    if selected == "Upload new SSH key":
                        ssh_key_file = input("Enter path to SSH public key file: ").strip()
                        if ssh_key_file and os.path.exists(ssh_key_file):
                            config['ssh_key_file'] = ssh_key_file
                        else:
                            print(f"{Colors.RED}SSH key file not found{Colors.NC}")
                    else:
                        config['ssh_key'] = selected
                else:
                    config['ssh_key'] = ssh_key
            else:
                config['ssh_key'] = ssh_key
        else:
            config['ssh_key'] = args.ssh_key
        
        # Volume
        if args.interactive and not args.volume_size:
            try:
                volume_size = input("Volume size in GB (0 for no volume): ").strip()
                config['volume_size'] = int(volume_size) if volume_size else 0
            except ValueError:
                config['volume_size'] = 0
        else:
            config['volume_size'] = args.volume_size or 0
        
        # Firewall
        if args.interactive and not args.firewall:
            print(f"{Colors.YELLOW}→{Colors.NC} Fetching available firewalls...")
            firewalls = self.get_firewalls()
            if firewalls:
                config['firewall'] = self.select_from_list("Select firewall:", firewalls, allow_none=True)
        else:
            config['firewall'] = args.firewall
        
        # Network
        if args.interactive and not args.network:
            print(f"{Colors.YELLOW}→{Colors.NC} Fetching available networks...")
            networks = self.get_networks()
            if networks:
                config['network'] = self.select_from_list("Select network:", networks, allow_none=True)
        else:
            config['network'] = args.network
        
        # Tags
        if args.interactive and not args.tags:
            tags = input("Tags (key:value,key:value format, leave empty for none): ").strip()
            config['tags'] = tags if tags else self.config.get('DEFAULT_TAGS', '')
        else:
            config['tags'] = args.tags or self.config.get('DEFAULT_TAGS', '')
        
        # Cloud-init config
        if args.interactive and not args.cloud_config:
            cloud_config = input("Cloud-init config file path (leave empty for none): ").strip()
            config['cloud_config'] = cloud_config
        else:
            config['cloud_config'] = args.cloud_config
        
        config['dry_run'] = args.dry_run
        
        return config
    
    def convert_tags(self, tags: str) -> str:
        """Convert tags from key:value to key=value format"""
        if not tags:
            return ""
        return tags.replace(':', '=')
    
    def create_volume(self, server_name: str, volume_size: int, location: str, dry_run: bool) -> Optional[str]:
        """Create a volume for the server"""
        volume_name = f"{server_name}-volume"
        
        print(f"{Colors.YELLOW}→{Colors.NC} Creating volume: {volume_name} ({volume_size}GB)")
        
        cmd = [
            'volume', 'create',
            '--name', volume_name,
            '--size', str(volume_size),
            '--location', location,
            '--format', 'ext4'
        ]
        
        if dry_run:
            print(f"{Colors.BLUE}[DRY RUN]{Colors.NC} Would create volume: hcloud {' '.join(cmd)}")
            return volume_name
        
        success, output = self.run_hcloud_command(cmd)
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Volume created successfully: {volume_name}")
            return volume_name
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to create volume: {output}")
            return None
    
    def upload_ssh_key(self, server_name: str, key_file: str, dry_run: bool) -> Optional[str]:
        """Upload SSH key from file"""
        if not os.path.exists(key_file):
            print(f"{Colors.RED}✗{Colors.NC} SSH key file not found: {key_file}")
            return None
        
        key_name = f"{server_name}-key-{int(time.time())}"
        
        print(f"{Colors.YELLOW}→{Colors.NC} Uploading SSH key: {key_name}")
        
        cmd = [
            'ssh-key', 'create',
            '--name', key_name,
            '--public-key-from-file', key_file
        ]
        
        if dry_run:
            print(f"{Colors.BLUE}[DRY RUN]{Colors.NC} Would upload SSH key: hcloud {' '.join(cmd)}")
            return key_name
        
        success, output = self.run_hcloud_command(cmd)
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} SSH key uploaded successfully: {key_name}")
            return key_name
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to upload SSH key: {output}")
            return None
    
    def deploy_server(self, server_name: str, config: Dict) -> bool:
        """Deploy a single server"""
        cmd = [
            'server', 'create',
            '--name', server_name,
            '--type', config['server_type'],
            '--image', config['image'],
            '--location', config['location']
        ]
        
        # Add SSH key
        if config.get('ssh_key'):
            cmd.extend(['--ssh-key', config['ssh_key']])
        
        # Add firewall
        if config.get('firewall'):
            cmd.extend(['--firewall', config['firewall']])
        
        # Add network
        if config.get('network'):
            cmd.extend(['--network', config['network']])
        
        # Add volume
        if config.get('volume_name'):
            cmd.extend(['--volume', config['volume_name']])
        
        # Add tags
        if config.get('tags'):
            converted_tags = self.convert_tags(config['tags'])
            cmd.extend(['--label', converted_tags])
        
        # Add cloud-init config
        if config.get('cloud_config') and os.path.exists(config['cloud_config']):
            cmd.extend(['--user-data-from-file', config['cloud_config']])
        
        print(f"{Colors.YELLOW}→{Colors.NC} Deploying server: {server_name}")
        print(f"{Colors.BLUE}Command:{Colors.NC} hcloud {' '.join(cmd)}")
        
        if config['dry_run']:
            print(f"{Colors.BLUE}[DRY RUN]{Colors.NC} Would execute: hcloud {' '.join(cmd)}")
            return True
        
        success, output = self.run_hcloud_command(cmd)
        if success:
            print(f"{Colors.GREEN}✓{Colors.NC} Server deployed successfully: {server_name}")
            
            # Wait for server to be ready and get IP
            print(f"{Colors.YELLOW}→{Colors.NC} Waiting for server to be ready...")
            time.sleep(3)
            
            # Get server info with JSON output for parsing
            success, info = self.run_hcloud_command(['server', 'describe', server_name, '-o', 'json'])
            if success:
                try:
                    server_data = json.loads(info)
                    public_ip = server_data.get('public_net', {}).get('ipv4', {}).get('ip', 'N/A')
                    private_ip = server_data.get('private_net', [{}])[0].get('ip', 'N/A') if server_data.get('private_net') else 'N/A'
                    
                    print(f"\n{Colors.GREEN}🎉 Deployment Complete!{Colors.NC}")
                    print("=" * 25)
                    print(f"{Colors.BLUE}Server:{Colors.NC} {server_name}")
                    print(f"{Colors.BLUE}Public IP:{Colors.NC} {public_ip}")
                    if private_ip != 'N/A':
                        print(f"{Colors.BLUE}Private IP:{Colors.NC} {private_ip}")
                    print(f"{Colors.BLUE}Location:{Colors.NC} {config['location']}")
                    print(f"{Colors.BLUE}Type:{Colors.NC} {config['server_type']}")
                    print(f"{Colors.BLUE}Image:{Colors.NC} {config['image']}")
                    
                    # SSH connection commands
                    if public_ip != 'N/A':
                        print(f"\n{Colors.CYAN}🔗 SSH Connection Commands:{Colors.NC}")
                        print("=" * 30)
                        
                        # Determine default user based on image
                        default_user = 'root'
                        image_lower = config['image'].lower()
                        if 'ubuntu' in image_lower:
                            default_user = 'ubuntu'
                        elif 'debian' in image_lower:
                            default_user = 'debian'
                        elif 'centos' in image_lower or 'rocky' in image_lower or 'almalinux' in image_lower:
                            default_user = 'centos'
                        elif 'fedora' in image_lower:
                            default_user = 'fedora'
                        elif 'opensuse' in image_lower:
                            default_user = 'opensuse'
                        
                        print(f"{Colors.YELLOW}# Direct SSH (using default user):{Colors.NC}")
                        print(f"ssh {default_user}@{public_ip}")
                        
                        print(f"\n{Colors.YELLOW}# SSH with custom user:{Colors.NC}")
                        print(f"ssh your_username@{public_ip}")
                        
                        print(f"\n{Colors.YELLOW}# SSH with specific key file:{Colors.NC}")
                        print(f"ssh -i ~/.ssh/your_key {default_user}@{public_ip}")
                        
                        print(f"\n{Colors.YELLOW}# Using Hetzner CLI (if configured):{Colors.NC}")
                        print(f"python3 manage.py ssh {server_name}")
                        
                        print(f"\n{Colors.GREEN}💡 Tip:{Colors.NC} Server may take 1-2 minutes to fully boot and accept SSH connections")
                        
                except json.JSONDecodeError:
                    print(f"{Colors.BLUE}Server details:{Colors.NC}")
                    print(info)
            else:
                print(f"{Colors.YELLOW}⚠{Colors.NC} Server deployed but couldn't retrieve details")
            
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Failed to deploy server: {output}")
            return False
    
    def deploy(self, args):
        """Main deployment function"""
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        if not self.validate_token():
            return False
        
        # Get configuration
        config = self.interactive_config(args)
        if not config:
            return False
        
        print(f"\n{Colors.BLUE}Hetzner Cloud Server Deployment{Colors.NC}")
        print("=" * 33)
        
        # Display configuration
        print(f"{Colors.BLUE}Configuration:{Colors.NC}")
        print(f"  Server Name: {config['name']}")
        print(f"  Server Count: {config['count']}")
        print(f"  Server Type: {config['server_type']}")
        print(f"  Image: {config['image']}")
        print(f"  Location: {config['location']}")
        print(f"  SSH Key: {config.get('ssh_key', 'None')}")
        print(f"  Volume: {config['volume_size']}GB" if config['volume_size'] > 0 else "  Volume: None")
        print(f"  Firewall: {config.get('firewall', 'None')}")
        print(f"  Network: {config.get('network', 'None')}")
        print(f"  Tags: {config.get('tags', 'None')}")
        print(f"  Cloud-Init Config: {config.get('cloud_config', 'None')}")
        print(f"  Dry Run: {config['dry_run']}")
        print()
        
        # Handle SSH key upload if needed
        if config.get('ssh_key_file'):
            uploaded_key = self.upload_ssh_key(config['name'], config['ssh_key_file'], config['dry_run'])
            if uploaded_key:
                config['ssh_key'] = uploaded_key
            else:
                return False
        
        # Deploy servers
        success_count = 0
        for i, server_name in enumerate(config['server_names']):
            print(f"{Colors.PURPLE}{'=' * 39}{Colors.NC}")
            print(f"{Colors.BLUE}Deploying server {i+1}/{config['count']}: {server_name}{Colors.NC}")
            print(f"{Colors.PURPLE}{'=' * 39}{Colors.NC}")
            
            # Create volume if needed
            if config['volume_size'] > 0:
                volume_name = self.create_volume(server_name, config['volume_size'], config['location'], config['dry_run'])
                if volume_name:
                    config['volume_name'] = volume_name
                else:
                    print(f"{Colors.RED}✗{Colors.NC} Failed to create volume for {server_name}")
                    continue
            
            # Deploy server
            if self.deploy_server(server_name, config):
                success_count += 1
                print(f"{Colors.GREEN}✓{Colors.NC} Server {i+1}/{config['count']} deployed successfully!")
            else:
                print(f"{Colors.RED}✗{Colors.NC} Failed to deploy server {i+1}/{config['count']}")
            
            print()
        
        # Final summary
        if not config['dry_run']:
            print(f"{Colors.GREEN}🎉 Deployment completed successfully!{Colors.NC}")
            print(f"Successfully deployed {success_count}/{config['count']} servers")
            
            print(f"{Colors.BLUE}Next steps:{Colors.NC}")
            if config['count'] == 1:
                server_name = config['name']
                print(f"  • SSH into your server: ssh root@$(hcloud server ip {server_name})")
                print(f"  • View server details: hcloud server describe {server_name}")
                print(f"  • Delete server: hcloud server delete {server_name}")
            else:
                base_name = config['name']
                print(f"  • List all servers: hcloud server list | grep {base_name}")
                print(f"  • SSH into first server: ssh root@$(hcloud server ip {base_name}-001)")
                print(f"  • View server details: hcloud server describe {base_name}-001")
                print(f"  • Delete all servers: for i in {{001..{config['count']:03d}}}; do hcloud server delete {base_name}-$i; done")
            
            if config['volume_size'] > 0:
                print(f"  • List volumes: hcloud volume list | grep {config['name']}")
        
        return success_count == config['count']

def main():
    parser = argparse.ArgumentParser(
        description='Hetzner Cloud Server Deployment Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -n my-server                    # Interactive deployment
  %(prog)s -n web-server -i ubuntu-24.04  # Deploy with specific image
  %(prog)s -n cluster -c 3 -s cpx21       # Deploy 3 servers
  %(prog)s --interactive                   # Full interactive mode
  %(prog)s -n test --dry-run               # Preview deployment
        """
    )
    
    # Required arguments
    parser.add_argument('-n', '--name', help='Server name')
    parser.add_argument('-t', '--token', help='Hetzner Cloud API token')
    
    # Server configuration
    parser.add_argument('-s', '--server-type', help='Server type (e.g., cpx11, cpx21)')
    parser.add_argument('-i', '--image', help='Server image (e.g., ubuntu-24.04)')
    parser.add_argument('-l', '--location', help='Server location (e.g., nbg1, ash)')
    parser.add_argument('-c', '--count', type=int, help='Number of instances to create (default: 1)')
    
    # Optional features
    parser.add_argument('-k', '--ssh-key', help='SSH key name')
    parser.add_argument('-v', '--volume-size', type=int, help='Volume size in GB')
    parser.add_argument('-w', '--firewall', help='Firewall name')
    parser.add_argument('--network', help='Network name')
    parser.add_argument('--tags', help='Tags in key:value,key:value format')
    parser.add_argument('--cloud-config', help='Path to cloud-init configuration file')
    
    # Mode options
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--dry-run', action='store_true', help='Show commands without executing')
    
    args = parser.parse_args()
    
    # Set token from command line if provided
    deployer = HetznerDeployer()
    if args.token:
        deployer.config['HETZNER_TOKEN'] = args.token
    
    # Check if we need interactive mode
    if args.interactive or not args.name or not args.image:
        args.interactive = True
    
    try:
        success = deployer.deploy(args)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Deployment cancelled by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.NC}")
        sys.exit(1)

if __name__ == '__main__':
    main()
