#!/bin/bash
# Kathara Test Lab Management Script for ICMP Smurf Attack Simulation
# Small 4-machine configuration for initial testing

LAB_DIR="/Users/mohammad/Downloads/coding/sec_project"
LAB_NAME="smurf_test_lab"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}ICMP Smurf Attack TEST Lab Manager${NC}"
    echo -e "${BLUE}4 Machines: Attacker + Victim + 2 Amplifiers${NC}"
    echo -e "${BLUE}=================================${NC}"
}

print_usage() {
    echo "Usage: $0 {start|stop|restart|status|connect|monitor|clean|copy|attack|test}"
    echo ""
    echo "Commands:"
    echo "  start     - Start the test lab (4 machines)"
    echo "  stop      - Stop the lab"
    echo "  restart   - Restart the lab"
    echo "  status    - Show lab status"
    echo "  connect   - Connect to a machine"
    echo "  monitor   - Monitor traffic"
    echo "  copy      - Copy attack files"
    echo "  attack    - Launch test attack"
    echo "  test      - Run connectivity tests"
    echo "  clean     - Clean up lab"
}

start_lab() {
    echo -e "${YELLOW}Starting ICMP Smurf Attack TEST Lab...${NC}"
    
    cd "$LAB_DIR"
    
    echo "Starting Kathara test lab with 4 machines..."
    echo "This should take 1-2 minutes..."
    
    # Use the test configuration by temporarily renaming files
    mv lab.conf lab_full.conf.backup 2>/dev/null || true
    mv lab_test.conf lab.conf
    
    export KATHARA_DOCKER_ARGS="--privileged"
    kathara lstart

    
    # Restore original configuration
    mv lab.conf lab_test.conf
    mv lab_full.conf.backup lab.conf 2>/dev/null || true
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Test lab started successfully!${NC}"
        echo ""
        echo "Machines created:"
        echo "  - Attacker: 192.168.1.100"
        echo "  - Victim: 192.168.1.50" 
        echo "  - Amplifier1: 192.168.1.11"
        echo "  - Amplifier2: 192.168.1.12"
        echo ""
        echo "Expected amplification: 1 packet → 2 responses"
        echo ""
        echo "Next steps:"
        echo "  1. Wait 1 minute for configuration"
        echo "  2. Copy files: $0 copy"
        echo "  3. Test connectivity: $0 test"
        echo "  4. Run attack: $0 attack"
    else
        echo -e "${RED}Failed to start test lab!${NC}"
        exit 1
    fi
}

stop_lab() {
    echo -e "${YELLOW}Stopping test lab...${NC}"
    cd "$LAB_DIR"
    kathara lclean
    echo -e "${GREEN}Test lab stopped.${NC}"
}

copy_files() {
    echo -e "${YELLOW}Copying attack files to test machines...${NC}"
    cd "$LAB_DIR"

    # Find the real Docker container name for the attacker
    attacker_container=$(docker ps -a --filter "name=_attacker_" --format '{{.Names}}' | head -n 1)

    if [ -z "$attacker_container" ]; then
        echo -e "${RED}Attacker container not found (is the lab running?)${NC}"
        return 1
    fi

    echo "Attacker container: $attacker_container"
    echo "Copying icmp_smurf_attack.py → /root/ inside attacker..."

    # Copy and chmod
    if docker cp icmp_smurf_attack.py "${attacker_container}":/root/ \
       && docker exec "${attacker_container}" chmod +x /root/icmp_smurf_attack.py; then
        echo -e "${GREEN}Files copied successfully!${NC}"
    else
        echo -e "${RED}docker cp failed – aborting.${NC}"
        return 1
    fi
}


test_connectivity() {
    echo -e "${YELLOW}Testing network connectivity...${NC}"
    cd "$LAB_DIR"
    
    echo "1. Testing attacker to victim connectivity..."
    kathara exec attacker "ping -c 2 192.168.1.50"
    
    echo ""
    echo "2. Testing attacker to amplifiers..."
    kathara exec attacker "ping -c 1 192.168.1.11"
    kathara exec attacker "ping -c 1 192.168.1.12"
    
    echo ""
    echo "3. Testing broadcast ping..."
    kathara exec attacker "ping -b -c 1 192.168.1.255"
    
    echo ""
    echo "4. Checking ICMP settings on amplifiers..."
    echo "Amplifier1 ICMP broadcast setting:"
    kathara exec amplifier1 "cat /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts"
    echo "Amplifier2 ICMP broadcast setting:"
    kathara exec amplifier2 "cat /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts"
    
    echo -e "${GREEN}Connectivity test completed!${NC}"
}

show_status() {
    echo -e "${BLUE}Test Lab Status:${NC}"
    cd "$LAB_DIR"
    kathara linfo
    
    echo ""
    echo -e "${BLUE}Network Configuration:${NC}"
    echo "Network: 192.168.1.0/24"
    echo "Broadcast: 192.168.1.255"
    echo "Attacker: 192.168.1.100"
    echo "Victim: 192.168.1.50"
    echo "Amplifier1: 192.168.1.11"
    echo "Amplifier2: 192.168.1.12"
    echo "Expected amplification: 1→2 (2x factor)"
}

connect_machine() {
    if [ -z "$1" ]; then
        echo "Available machines:"
        echo "  - attacker (192.168.1.100)"
        echo "  - victim (192.168.1.50)"
        echo "  - amplifier1 (192.168.1.11)"
        echo "  - amplifier2 (192.168.1.12)"
        echo ""
        read -p "Enter machine name: " machine
    else
        machine="$1"
    fi
    
    echo -e "${YELLOW}Connecting to $machine...${NC}"
    cd "$LAB_DIR"
    kathara connect "$machine"
}

monitor_traffic() {
    machine="${1:-victim}"
    
    echo -e "${YELLOW}Monitoring ICMP traffic on $machine...${NC}"
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    cd "$LAB_DIR"
    kathara exec "$machine" "tcpdump -i eth0 -n icmp"
}

launch_test_attack() {
    echo -e "${YELLOW}Launching TEST ICMP Smurf Attack...${NC}"
    echo ""
    echo "Test Attack Parameters:"
    echo "  Victim: 192.168.1.50"
    echo "  Broadcast: 192.168.1.255"
    echo "  Rate: 5 packets/second (low for testing)"
    echo "  Duration: 20 seconds"
    echo "  Expected amplification: 1 packet → 2 responses"
    echo ""
    
    read -p "Continue with test attack? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        cd "$LAB_DIR"
        echo "Launching test attack..."
        kathara exec attacker -- \
          python3 /root/icmp_smurf_attack.py \
            -v 192.168.1.50 -b 192.168.1.255 -r 5 -d 20
    else
        echo "Test attack cancelled."
    fi
}



clean_lab() {
    echo -e "${YELLOW}Cleaning up test lab...${NC}"
    cd "$LAB_DIR"
    kathara lclean
    echo -e "${GREEN}Test lab cleaned.${NC}"
}

# Main script logic
case "$1" in
    start)
        print_header
        start_lab
        ;;
    stop)
        print_header
        stop_lab
        ;;
    restart)
        print_header
        stop_lab
        sleep 2
        start_lab
        ;;
    status)
        print_header
        show_status
        ;;
    connect)
        print_header
        connect_machine "$2"
        ;;
    monitor)
        print_header
        monitor_traffic "$2"
        ;;
    copy)
        print_header
        copy_files
        ;;
    test)
        print_header
        test_connectivity
        ;;
    attack)
        print_header
        launch_test_attack
        ;;
    clean)
        print_header
        clean_lab
        ;;
    *)
        print_header
        print_usage
        exit 1
        ;;
esac
