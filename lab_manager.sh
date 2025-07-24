#!/bin/bash
# Kathara Lab Management Script for ICMP Smurf Attack Simulation

LAB_DIR="/Users/mohammad/Downloads/coding/sec_project"
LAB_NAME="smurf_attack_lab"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}ICMP Smurf Attack Lab Manager${NC}"
    echo -e "${BLUE}=================================${NC}"
}

print_usage() {
    echo "Usage: $0 {start|stop|restart|status|connect|monitor|clean|copy|attack}"
    echo ""
    echo "Commands:"
    echo "  start     - Start the Kathara lab"
    echo "  stop      - Stop the lab (graceful shutdown)"
    echo "  restart   - Restart the lab"
    echo "  status    - Show lab status and machine list"
    echo "  connect   - Connect to a specific machine"
    echo "  monitor   - Monitor attack traffic"
    echo "  clean     - Clean up lab files and processes"
    echo "  copy      - Copy attack files to machines"
    echo "  attack    - Launch attack with common parameters"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start the lab"
    echo "  $0 copy                     # Copy attack files to machines"
    echo "  $0 connect attacker         # Connect to attacker machine"
    echo "  $0 connect victim           # Connect to victim machine"
    echo "  $0 monitor victim           # Monitor victim traffic"
}

start_lab() {
    echo -e "${YELLOW}Starting ICMP Smurf Attack Lab...${NC}"
    
    if [ ! -f "$LAB_DIR/lab.conf" ]; then
        echo -e "${RED}Error: lab.conf not found in $LAB_DIR${NC}"
        exit 1
    fi
    
    cd "$LAB_DIR"
    
    echo "Starting Kathara lab with 27 machines..."
    echo "This may take 2-3 minutes..."
    
    export KATHARA_DOCKER_ARGS="--privileged"
    kathara lstart
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Lab started successfully!${NC}"
        echo ""
        echo "Machines created:"
        echo "  - Attacker: 192.168.1.100"
        echo "  - Victim: 192.168.1.50" 
        echo "  - Amplifiers: 192.168.1.11-35 (25 machines)"
        echo ""
        echo "Next steps:"
        echo "  1. Wait 1-2 minutes for all machines to configure"
        echo "  2. Copy attack script: kathara cp icmp_smurf_attack.py attacker:/root/"
        echo "  3. Connect to attacker: $0 connect attacker"
        echo "  4. Run attack: python3 icmp_smurf_attack.py -v 192.168.1.50 -b 192.168.1.255"
    else
        echo -e "${RED}Failed to start lab!${NC}"
        exit 1
    fi
}

stop_lab() {
    echo -e "${YELLOW}Stopping ICMP Smurf Attack Lab...${NC}"
    cd "$LAB_DIR"
    kathara lclean
    echo -e "${GREEN}Lab stopped.${NC}"
}

restart_lab() {
    echo -e "${YELLOW}Restarting ICMP Smurf Attack Lab...${NC}"
    stop_lab
    sleep 3
    start_lab
}

show_status() {
    echo -e "${BLUE}Lab Status:${NC}"
    cd "$LAB_DIR"
    kathara linfo
    
    echo ""
    echo -e "${BLUE}Network Configuration:${NC}"
    echo "Network: 192.168.1.0/24"
    echo "Broadcast: 192.168.1.255"
    echo "Attacker: 192.168.1.100"
    echo "Victim: 192.168.1.50"
    echo "Amplifiers: 192.168.1.11-35"
}

connect_machine() {
    if [ -z "$1" ]; then
        echo "Available machines:"
        echo "  - attacker (192.168.1.100)"
        echo "  - victim (192.168.1.50)"
        echo "  - amplifier1-amplifier25 (192.168.1.11-35)"
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
    
    echo -e "${YELLOW}Monitoring traffic on $machine...${NC}"
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    cd "$LAB_DIR"
    kathara exec "$machine" tcpdump -i eth0 -n icmp
}

clean_lab() {
    echo -e "${YELLOW}Cleaning up lab...${NC}"
    cd "$LAB_DIR"
    kathara lclean
    echo -e "${GREEN}Lab cleaned.${NC}"
}

launch_attack() {
    echo -e "${YELLOW}Launching ICMP Smurf Attack...${NC}"
    echo ""
    echo "Attack Parameters:"
    echo "  Victim: 192.168.1.50"
    echo "  Broadcast: 192.168.1.255"
    echo "  Rate: 10 packets/second"
    echo "  Duration: 60 seconds"
    echo ""
    
    read -p "Continue with attack? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        cd "$LAB_DIR"
        
        echo "Launching attack..."
        kathara exec attacker -- \
          python3 /root/icmp_smurf_attack.py \
            -v 192.168.1.50 -b 192.168.1.255 -r 10 -d 60
    else
        echo "Attack cancelled."
    fi
}

copy_files() {
    echo -e "${YELLOW}Copying attack files to machines...${NC}"
    cd "$LAB_DIR"
    
    # Find the real Docker container name for the attacker
    attacker_container=$(docker ps -a --filter "name=_attacker_" --format '{{.Names}}' | head -n 1)

    if [ -z "$attacker_container" ]; then
        echo -e "${RED}Attacker container not found (is the lab running?)${NC}"
        return 1
    fi

    echo "Attacker container: $attacker_container"
    echo "Copying icmp_smurf_attack.py → /root/ inside attacker..."

    # Copy and chmod attack script
    if docker cp icmp_smurf_attack.py "${attacker_container}":/root/ \
       && docker exec "${attacker_container}" chmod +x /root/icmp_smurf_attack.py; then
        echo "icmp_smurf_attack.py copied successfully"
    else
        echo -e "${RED}Failed to copy icmp_smurf_attack.py${NC}"
        return 1
    fi
    
    # Copy and chmod test script
    echo "Copying test_attack_tool.py → /root/ inside attacker..."
    if docker cp test_attack_tool.py "${attacker_container}":/root/ \
       && docker exec "${attacker_container}" chmod +x /root/test_attack_tool.py; then
        echo "test_attack_tool.py copied successfully"
    else
        echo -e "${RED}Failed to copy test_attack_tool.py${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Files copied successfully!${NC}"
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
        restart_lab
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
    clean)
        print_header
        clean_lab
        ;;
    copy)
        print_header
        copy_files
        ;;
    attack)
        print_header
        launch_attack
        ;;
    *)
        print_header
        print_usage
        exit 1
        ;;
esac
