# ICMP Smurf Attack Educational Simulation

## Project Overview

This project provides a complete educational simulation of the ICMP Smurf attack, demonstrating how broadcast amplification attacks work in network security. It includes custom-built attack tools and a comprehensive Kathara network simulation environment.

## Project Structure

```
sec_project/
├── icmp_smurf_attack.py     # Main attack tool (custom packet crafting)
├── lab.conf                 # Kathara lab configuration
├── attacker.startup         # Attacker machine configuration
├── victim.startup           # Victim machine configuration
├── amplifier*.startup       # 25 amplifier machine configurations
├── topology_diagram.md      # Network topology documentation
├── README.md               # This file
└── ins.md                  # Original assignment instructions
```

## Attack Tool Features

### Custom Implementation

- **Raw Socket Programming**: Complete IP and ICMP packet crafting from scratch
- **No External Libraries**: Uses only standard Python libraries (socket, struct)
- **IP Spoofing**: Implements source IP address spoofing
- **Checksum Calculation**: Custom Internet checksum algorithm (RFC 1071)
- **Broadcast Support**: Sends packets to broadcast addresses

### Packet Crafting Details

- **IP Header**: Complete IPv4 header construction with all fields
- **ICMP Header**: ICMP Echo Request packets with custom payloads
- **Attack Signature**: Embedded attack identification in packets
- **Timestamp Tracking**: Packet timing for analysis

### Monitoring and Statistics

- **Real-time Statistics**: Packets sent, transmission rate, duration
- **Attack Visualization**: Live packet transmission logging
- **Amplification Calculation**: Potential amplification factor display
- **Error Handling**: Comprehensive error checking and reporting

## Network Simulation Setup

### Prerequisites

- **Kathara Network Simulator**: Install from https://www.kathara.org/
- **Linux Environment**: Required for Kathara and raw sockets
- **Root Privileges**: Needed for raw socket operations

### Lab Configuration

- **Topology**: Single broadcast domain with 27 machines total
- **Attacker**: 1 machine (192.168.1.100)
- **Victim**: 1 machine (192.168.1.50)
- **Amplifiers**: 25 machines (192.168.1.11-35)
- **Network**: 192.168.1.0/24 subnet
- **Broadcast**: 192.168.1.255

## Installation and Setup

### 1. Install Kathara

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install kathara

# Or download from official website
wget https://github.com/KatharaFramework/Kathara/releases/latest
```

### 2. Prepare the Lab

```bash
# Clone or create project directory
mkdir sec_project
cd sec_project

# Copy all lab files (lab.conf, *.startup, *.py)
# Files should be in the same directory
```

### 3. Start the Kathara Lab

```bash
# Navigate to project directory
cd sec_project

# Start the lab (this will create all 27 machines)
kathara lstart

# Wait for all machines to boot and configure
# This may take 2-3 minutes
```

### 4. Verify Network Setup

```bash
# Connect to attacker machine
kathara connect attacker

# Test connectivity to victim
ping 192.168.1.50

# Test broadcast connectivity
ping -b 192.168.1.255

# List all machines in network
nmap -sn 192.168.1.0/24
```

## Running the Attack

### 1. Copy Attack Tool to Attacker Machine

```bash
# Method 1: Using the lab manager script (recommended)
./lab_manager.sh copy

# Method 2: Manual copy using kathara exec
cat icmp_smurf_attack.py | kathara exec attacker "cat > /root/icmp_smurf_attack.py"
kathara exec attacker "chmod +x /root/icmp_smurf_attack.py"

# Method 3: Copy via shared directory (if available)
# Setup shared directory in lab.conf and copy files there
```

### 2. Connect to Attacker Machine

```bash
kathara connect attacker
cd /root
```

### 3. Execute the Attack

```bash
# Basic attack (60 seconds, 10 pps)
python3 icmp_smurf_attack.py -v 192.168.1.50 -b 192.168.1.255

# High-rate attack (30 seconds, 50 pps)
python3 icmp_smurf_attack.py -v 192.168.1.50 -b 192.168.1.255 -r 50 -d 30

# Continuous attack with larger payloads
python3 icmp_smurf_attack.py -v 192.168.1.50 -b 192.168.1.255 -r 20 -d 0 -s 64
```

### 4. Command Line Options

```
-v, --victim       Target victim IP address (required)
-b, --broadcast    Broadcast IP address (required)
-r, --rate         Packets per second (default: 10)
-d, --duration     Attack duration in seconds (default: 60, 0=infinite)
-s, --size         ICMP payload size in bytes (default: 32)
-i, --interface    Network interface (auto-detect)
--list-interfaces  Show available interfaces
```

## Monitoring the Attack

### 1. Monitor Victim Machine

```bash
# Connect to victim in separate terminal
kathara connect victim

# Monitor incoming ICMP traffic
/root/monitor_traffic.sh

# Monitor system resources
/root/monitor_resources.sh

# Check network statistics
iftop -i eth0
```

### 2. Monitor Amplifier Machines

```bash
# Connect to any amplifier
kathara connect amplifier1

# Monitor ICMP responses
/root/monitor_icmp.sh

# Check if responding to broadcasts
tcpdump -i eth0 -n "icmp and dst 192.168.1.255"
```

### 3. Network-wide Analysis

```bash
# From any machine, capture all ICMP traffic
tcpdump -i eth0 -n -w attack_capture.pcap icmp

# Analyze with tcpdump
tcpdump -r attack_capture.pcap -n icmp | head -50
```

## Expected Attack Results

### Amplification Effect

- **1 packet sent** by attacker → **25 packets received** by victim
- **Amplification Factor**: 25:1 ratio
- **Traffic Multiplication**: 25x bandwidth consumption on victim

### Attack Characteristics

- Victim receives continuous ICMP Echo Reply flood
- Each spoofed broadcast request triggers multiple responses
- Victim's network interface becomes saturated
- Legitimate traffic to victim may be impacted

### Observable Metrics

- **Packet Rate**: 10 pps attack → 250 pps received by victim
- **Bandwidth**: 32-byte payloads → ~2KB/s becomes ~50KB/s
- **CPU Impact**: ICMP processing load on victim machine
- **Network Congestion**: Interface utilization increases

## Educational Analysis Points

### 1. Attack Mechanics

- **IP Spoofing**: How source address forgery enables redirection
- **Broadcast Amplification**: Why broadcast domains multiply traffic
- **Protocol Exploitation**: ICMP echo request/reply behavior
- **Network Layer Vulnerabilities**: L3 protocol weaknesses

### 2. Mitigation Strategies

- **Ingress Filtering**: Prevent IP spoofing at network borders
- **Broadcast Limiting**: Disable ICMP broadcast responses
- **Rate Limiting**: Implement ICMP rate controls
- **Network Segmentation**: Reduce broadcast domain size

### 3. Detection Methods

- **Traffic Analysis**: Unusual ICMP patterns and volumes
- **Source Verification**: Inconsistent source addresses
- **Timing Analysis**: Synchronized response patterns
- **Baseline Comparison**: Normal vs. attack traffic profiles

## Troubleshooting

### Common Issues

#### 1. Raw Socket Permission Errors

```bash
# Ensure running with root privileges
sudo python3 icmp_smurf_attack.py -v 192.168.1.50 -b 192.168.1.255
```

#### 2. No Amplification Observed

```bash
# Check amplifier ICMP settings
echo 0 > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts
echo 0 > /proc/sys/net/ipv4/icmp_echo_ignore_all

# Verify broadcast connectivity
ping -b 192.168.1.255
```

#### 3. Network Connectivity Issues

```bash
# Check interface configuration
ip addr show eth0
ip route show

# Verify broadcast domain
ping -b -c 1 192.168.1.255
```

#### 4. Kathara Lab Issues

```bash
# Restart lab if machines don't communicate
kathara lclean
kathara lstart

# Check lab status
kathara linfo
```

### Performance Optimization

#### For Higher Amplification

- Increase number of amplifier machines in lab.conf
- Add more IP addresses to amplifier startup scripts
- Use larger broadcast domains (/16 instead of /24)

#### For Realistic Testing

- Add network latency simulation
- Implement bandwidth limitations
- Include firewall/IDS detection simulation

## Safety and Legal Considerations

### Educational Use Only

- This tool is designed for cybersecurity education
- Use only in controlled lab environments
- Never use against networks you don't own
- Obtain proper authorization before any testing

### Responsible Disclosure

- Understand attack mechanics for defensive purposes
- Report vulnerabilities through proper channels
- Follow responsible disclosure practices
- Respect network owner policies

## Advanced Exercises

### 1. Attack Variations

- Modify payload sizes and analyze impact
- Test different packet rates and patterns
- Implement fragmented packet attacks
- Try different ICMP types and codes

### 2. Defense Implementation

- Add ingress filtering to lab topology
- Implement ICMP rate limiting
- Create IDS signatures for detection
- Design network segmentation strategies

### 3. Analysis and Research

- Measure exact amplification factors
- Analyze network protocol behavior
- Compare with other DDoS attack types
- Study real-world attack incidents

## References and Further Reading

### Technical Standards

- RFC 792: Internet Control Message Protocol
- RFC 791: Internet Protocol Specification
- RFC 1071: Computing the Internet Checksum
- RFC 2827: Network Ingress Filtering

### Security Resources

- NIST Cybersecurity Framework
- OWASP Testing Guide
- SANS Network Security Resources
- Academic papers on DDoS amplification attacks

---

**Disclaimer**: This educational simulation is provided for learning purposes only. Users are responsible for ensuring legal and ethical use of these tools and techniques.
