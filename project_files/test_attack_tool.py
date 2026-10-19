#!/usr/bin/env python3
"""
ICMP Smurf Attack Tool Test Suite
"""

import sys
import os
import socket

# Add current directory to path to import the attack tool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from icmp_smurf_attack import PacketCrafter, SmurfAttacker, calculate_broadcast_address
    print("[+] Successfully imported attack tool modules")
except ImportError as e:
    print(f"[-] Failed to import attack tool: {e}")
    sys.exit(1)

def test_packet_crafter():
    """Test the PacketCrafter class functionality"""
    print("\n=== Testing PacketCrafter ===")
    
    crafter = PacketCrafter()
    print("[+] PacketCrafter initialized")
    
    # Test checksum calculation
    test_data = b"Hello World"
    checksum = crafter.calculate_checksum(test_data)
    print(f"[+] Checksum calculation test: {checksum:04x}")
    
    # Test IP header crafting
    try:
        ip_header = crafter.craft_ip_header(
            src_ip="192.168.1.100",
            dst_ip="192.168.1.255", 
            payload_length=32
        )
        print(f"[+] IP header crafted: {len(ip_header)} bytes")
        
        # Verify IP header structure
        if len(ip_header) == 20:  # Standard IP header size
            print("[+] IP header size correct")
        else:
            print(f"[-] IP header size incorrect: {len(ip_header)} bytes")
            
    except Exception as e:
        print(f"[-] IP header crafting failed: {e}")
        return False
    
    # Test ICMP header crafting
    try:
        icmp_packet = crafter.craft_icmp_header()
        print(f"[+] ICMP packet crafted: {len(icmp_packet)} bytes")
        
        # Verify ICMP packet has header + payload
        if len(icmp_packet) >= 8:  # Minimum ICMP header size
            print("[+] ICMP packet size valid")
        else:
            print(f"[-] ICMP packet too small: {len(icmp_packet)} bytes")
            
    except Exception as e:
        print(f"[-] ICMP header crafting failed: {e}")
        return False
    
    print("[+] PacketCrafter tests passed")
    return True

def test_address_validation():
    """Test IP address validation and broadcast calculation"""
    print("\n=== Testing Address Validation ===")
    
    # Test valid IP addresses
    valid_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
    for ip in valid_ips:
        try:
            socket.inet_aton(ip)
            print(f"[+] Valid IP: {ip}")
        except socket.error:
            print(f"[-] Invalid IP: {ip}")
            return False
    
    # Test broadcast calculation
    try:
        broadcast = calculate_broadcast_address("192.168.1.10")
        expected = "192.168.1.255"
        if broadcast == expected:
            print(f"[+] Broadcast calculation correct: {broadcast}")
        else:
            print(f"[-] Broadcast calculation incorrect: {broadcast} != {expected}")
            return False
    except Exception as e:
        print(f"[-] Broadcast calculation failed: {e}")
        return False
    
    print("[+] Address validation tests passed")
    return True

def test_smurf_attacker_init():
    """Test SmurfAttacker initialization without creating sockets"""
    print("\n=== Testing SmurfAttacker Initialization ===")
    
    # Mock socket creation to avoid requiring root privileges
    original_socket = socket.socket
    
    def mock_socket(*args, **kwargs):
        class MockSocket:
            def setsockopt(self, *args): pass
            def close(self): pass
        return MockSocket()
    
    # Temporarily replace socket creation
    socket.socket = mock_socket
    
    try:
        # Test with valid parameters
        attacker = SmurfAttacker.__new__(SmurfAttacker)
        attacker.victim_ip = "192.168.1.50"
        attacker.broadcast_ip = "192.168.1.255"
        attacker.packet_rate = 10
        attacker.payload_size = 32
        attacker.packets_sent = 0
        attacker.attack_active = False
        attacker.packet_crafter = PacketCrafter()
        
        print("[+] SmurfAttacker object created successfully")
        
        # Test packet crafting without sending
        packet = attacker.packet_crafter.craft_ip_header("192.168.1.50", "192.168.1.255", 32)
        packet += attacker.packet_crafter.craft_icmp_header()
        
        print(f"[+] Complete packet crafted: {len(packet)} bytes")
        
    except Exception as e:
        print(f"[-] SmurfAttacker initialization failed: {e}")
        return False
    finally:
        # Restore original socket
        socket.socket = original_socket
    
    print("[+] SmurfAttacker initialization tests passed")
    return True

def test_packet_structure():
    """Test the structure of crafted packets"""
    print("\n=== Testing Packet Structure ===")
    
    crafter = PacketCrafter()
    
    # Create a complete packet
    icmp_packet = crafter.craft_icmp_header(payload_data=b"TEST_PAYLOAD")
    ip_packet = crafter.craft_ip_header("192.168.1.100", "192.168.1.255", len(icmp_packet))
    complete_packet = ip_packet + icmp_packet
    
    print(f"[+] Complete packet size: {len(complete_packet)} bytes")
    
    # Analyze IP header
    if len(ip_packet) >= 20:
        version_ihl = ip_packet[0]
        version = (version_ihl >> 4) & 0x0F
        ihl = version_ihl & 0x0F
        
        if version == 4:
            print("[+] IPv4 version correct")
        else:
            print(f"[-] IPv4 version incorrect: {version}")
            return False
            
        if ihl == 5:  # 5 * 4 = 20 bytes
            print("[+] IP header length correct")
        else:
            print(f"[-] IP header length incorrect: {ihl}")
            return False
    
    # Analyze ICMP header
    if len(icmp_packet) >= 8:
        icmp_type = icmp_packet[0]
        icmp_code = icmp_packet[1]
        
        if icmp_type == 8:  # Echo Request
            print("[+] ICMP type correct (Echo Request)")
        else:
            print(f"[-] ICMP type incorrect: {icmp_type}")
            return False
            
        if icmp_code == 0:
            print("[+] ICMP code correct")
        else:
            print(f"[-] ICMP code incorrect: {icmp_code}")
            return False
    
    print("[+] Packet structure tests passed")
    return True

def main():
    """Run all tests"""
    print("ICMP Smurf Attack Tool Test Suite")
    print("=" * 50)
    
    tests = [
        test_packet_crafter,
        test_address_validation,
        test_smurf_attacker_init,
        test_packet_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"[-] Test {test.__name__} failed")
        except Exception as e:
            print(f"[-] Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[+] All tests passed! Attack tool is ready.")
        return 0
    else:
        print(f"[-] {total - passed} tests failed. Check implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
