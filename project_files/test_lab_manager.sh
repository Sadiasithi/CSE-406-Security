#!/bin/bash
# Kathara Test Lab Management Script for ICMP Smurf Attack Simulation
# Small 4-machine configuration for initial testing

LAB_DIR="/home/sadia-afrin-sithi/Downloads/sec_project"

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
    echo "Usage: $0 {start|stop|restart|status|connect|monitor|clean|copy|attack|test|measure|analyze}"
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
    echo "  measure   - Launch attack with success measurement"
    echo "  analyze   - Analyze last attack results"
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
    echo "Copying files to attacker machine..."

    # Copy attack script and monitor script
    if docker cp icmp_smurf_attack.py "${attacker_container}":/root/ \
       && docker cp attack_monitor.py "${attacker_container}":/root/ \
       && docker exec "${attacker_container}" chmod +x /root/icmp_smurf_attack.py \
       && docker exec "${attacker_container}" chmod +x /root/attack_monitor.py; then
        echo -e "${GREEN}Files copied successfully!${NC}"
        echo "  ✓ icmp_smurf_attack.py"
        echo "  ✓ attack_monitor.py"
    else
        echo -e "${RED}docker cp failed – aborting.${NC}"
        return 1
    fi
}


test_connectivity() {
    echo -e "${YELLOW}Testing network connectivity...${NC}"
    cd "$LAB_DIR"
    
    echo "1. Testing attacker to victim connectivity..."
    python -m kathara exec attacker "ping -c 2 192.168.1.50"
    
    echo ""
    echo "2. Testing attacker to amplifiers..."
    python -m kathara exec attacker "ping -c 1 192.168.1.11"
    python -m kathara exec attacker "ping -c 1 192.168.1.12"
    
    echo ""
    echo "3. Testing broadcast ping..."
    python -m kathara exec attacker "ping -b -c 1 192.168.1.255"
    
    echo ""
    echo "4. Checking ICMP settings on amplifiers..."
    echo "Amplifier1 ICMP broadcast setting:"
    python -m kathara exec amplifier1 "cat /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts"
    echo "Amplifier2 ICMP broadcast setting:"
    python -m kathara exec amplifier2 "cat /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts"
    
    echo -e "${GREEN}Connectivity test completed!${NC}"
}

show_status() {
    echo -e "${BLUE}Test Lab Status:${NC}"
    cd "$LAB_DIR"
    python -m kathara linfo
    
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
    python -m kathara connect "$machine"
}

monitor_traffic() {
    machine="${1:-victim}"
    
    echo -e "${YELLOW}Monitoring ICMP traffic on $machine...${NC}"
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    cd "$LAB_DIR"
    python -m kathara exec "$machine" "tcpdump -i eth0 -n icmp"
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
        python -m kathara exec attacker -- \
          python3 /root/icmp_smurf_attack.py \
            -v 192.168.1.50 -b 192.168.1.255 -r 5 -d 20
    else
        echo "Test attack cancelled."
    fi
}

measure_attack_success() {
    echo -e "${YELLOW}Launching Attack with Success Measurement...${NC}"
    echo ""
    echo "This will:"
    echo "  1. Start traffic monitoring on victim"
    echo "  2. Launch coordinated attack"
    echo "  3. Measure amplification factor"
    echo "  4. Calculate success percentage"
    echo ""
    
    # Get attack parameters
    read -p "Attack duration (seconds) [30]: " duration
    duration=${duration:-30}
    
    read -p "Attack rate (packets/second) [10]: " rate
    rate=${rate:-10}
    
    read -p "Continue with measured attack? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "Attack cancelled."
        return
    fi
    
    cd "$LAB_DIR"
    
    echo -e "${BLUE}Starting Attack Success Measurement...${NC}"
    echo "Duration: ${duration}s, Rate: ${rate} pps"
    echo "Expected packets sent: $((duration * rate))"
    echo ""
    
    # Start monitoring on victim (background)
    echo "1. Starting victim traffic monitoring..."
    python -m kathara exec victim -- bash -c "
        echo 'Starting tcpdump monitoring...'
        timeout $((duration + 10)) tcpdump -i eth0 -n -q 'icmp and dst 192.168.1.50' > /tmp/victim_traffic.log 2>&1 &
        echo 'Victim monitoring started'
    " &
    
    # Start monitoring on amplifiers (background)
    echo "2. Starting amplifier monitoring..."
    python -m kathara exec amplifier1 -- bash -c "
        timeout $((duration + 10)) tcpdump -i eth0 -n -q 'icmp and src 192.168.1.50' > /tmp/amp1_traffic.log 2>&1 &
    " &
    
    python -m kathara exec amplifier2 -- bash -c "
        timeout $((duration + 10)) tcpdump -i eth0 -n -q 'icmp and src 192.168.1.50' > /tmp/amp2_traffic.log 2>&1 &
    " &
    
    # Wait for monitoring to start
    sleep 3
    
    # Launch attack
    echo "3. Launching attack..."
    python -m kathara exec attacker -- \
      python3 /root/icmp_smurf_attack.py \
        -v 192.168.1.50 -b 192.168.1.255 -r $rate -d $duration
    
    # Wait for monitoring to complete
    echo "4. Waiting for monitoring to complete..."
    sleep 5
    
    # Collect and analyze results
    echo ""
    echo -e "${BLUE}ATTACK SUCCESS ANALYSIS${NC}"
    echo "=================================="
    
    # Count victim packets received
    victim_packets=$(python -m kathara exec victim -- bash -c "
        sleep 2
        if [ -f /tmp/victim_traffic.log ]; then
            grep -c 'ICMP' /tmp/victim_traffic.log 2>/dev/null || echo 0
        else
            echo 0
        fi
    ")
    
    # Count amplifier responses
    amp1_responses=$(python -m kathara exec amplifier1 -- bash -c "
        sleep 2
        if [ -f /tmp/amp1_traffic.log ]; then
            grep -c 'ICMP' /tmp/amp1_traffic.log 2>/dev/null || echo 0
        else
            echo 0
        fi
    ")
    
    amp2_responses=$(python -m kathara exec amplifier2 -- bash -c "
        sleep 2
        if [ -f /tmp/amp2_traffic.log ]; then
            grep -c 'ICMP' /tmp/amp2_traffic.log 2>/dev/null || echo 0
        else
            echo 0
        fi
    ")
    
    # Calculate metrics
    expected_packets=$((duration * rate))
    total_responses=$((amp1_responses + amp2_responses))
     if [ "$expected_packets" -gt 0 ]; then
        amplification_factor=$(awk "BEGIN {printf \"%.2f\", $victim_packets / $expected_packets}")
        success_percentage=$(awk "BEGIN {printf \"%.1f\", ($victim_packets / $expected_packets / 2) * 100}")
    else
        amplification_factor="0.00"
        success_percentage="0.0"
    fi    # ...existing code...
    
    # Calculate metrics
    expected_packets=$((duration * rate))
    total_responses=$((amp1_responses + amp2_responses))
    
    # Calculate metrics using awk for floating point math
    if [ "$expected_packets" -gt 0 ]; then
        # Calculate amplification factor (received/sent)
        amplification_factor=$(awk -v vp="$victim_packets" -v ep="$expected_packets" \
            'BEGIN {printf "%.2f", vp/ep}')
        
        # Calculate success percentage considering 2x amplification target
        success_percentage=$(awk -v vp="$victim_packets" -v ep="$expected_packets" \
            'BEGIN {printf "%.1f", (vp/(ep*2))*100}')
    else
        amplification_factor="0.00"
        success_percentage="0.0"
    fi
    
    # Determine responding amplifiers
    responding_amps=0
    [ "$amp1_responses" -gt 0 ] && ((responding_amps++))
    [ "$amp2_responses" -gt 0 ] && ((responding_amps++))
    
    # Calculate participation rate using awk
    participation_rate=$(awk -v ra="$responding_amps" \
        'BEGIN {printf "%.1f", (ra/2)*100}')
    
    # Success rating calculations using awk instead of bc
    success_rating=$(awk -v sp="$success_percentage" \
        'BEGIN {
            if (sp >= 80) print "1"
            else if (sp >= 60) print "2"
            else if (sp >= 30) print "3"
            else print "4"
        }')
    
    case "$success_rating" in
        1) rating="🔴 HIGHLY SUCCESSFUL" ;;
        2) rating="🟡 MODERATELY SUCCESSFUL" ;;
        3) rating="🟠 PARTIALLY SUCCESSFUL" ;;
        *) rating="🟢 INEFFECTIVE" ;;
    esac
    
    # ...existing code...
    # Determine responding amplifiers
    responding_amps=0
    if [ "$amp1_responses" -gt 0 ]; then
        responding_amps=$((responding_amps + 1))
    fi
    if [ "$amp2_responses" -gt 0 ]; then
        responding_amps=$((responding_amps + 1))
    fi
    
    participation_rate=$(echo "scale=1; ($responding_amps / 2) * 100" | bc -l 2>/dev/null || echo "0")
    
    # Display results
    echo ""
    echo "AMPLIFICATION ANALYSIS:"
    echo "  • Attack Packets Sent: $expected_packets"
    echo "  • Victim Packets Received: $victim_packets"
    echo "  • Amplification Factor: ${amplification_factor}x"
    echo "  • Theoretical Maximum: 2x"
    echo ""
    echo "AMPLIFIER PARTICIPATION:"
    echo "  • Amplifier1 (192.168.1.11): $amp1_responses responses"
    echo "  • Amplifier2 (192.168.1.12): $amp2_responses responses"
    echo "  • Responding Amplifiers: $responding_amps/2 (${participation_rate}%)"
    echo ""
    echo "ATTACK EFFECTIVENESS:"
    
    # Success rating
    res=$(echo "$success_percentage >= 80" | bc -l 2>/dev/null || echo 0)
    if [ "$res" -eq 1 ]; then
        rating="🔴 HIGHLY SUCCESSFUL"
    else
        res=$(echo "$success_percentage >= 60" | bc -l 2>/dev/null || echo 0)
        if [ "$res" -eq 1 ]; then
            rating="🟡 MODERATELY SUCCESSFUL"
        else
            res=$(echo "$success_percentage >= 30" | bc -l 2>/dev/null || echo 0)
            if [ "$res" -eq 1 ]; then
                rating="🟠 PARTIALLY SUCCESSFUL"
            else
                rating="🟢 INEFFECTIVE"
            fi
        fi
    fi
    
    echo "  • Success Percentage: ${success_percentage}%"
    echo "  • Overall Rating: $rating"
    echo ""
    
    # Recommendations
    echo "RECOMMENDATIONS:"
    res=$(echo "$participation_rate < 100" | bc -l 2>/dev/null || echo 0)
    if [ "$res" -eq 1 ]; then
        echo "  • Check ICMP broadcast settings on silent amplifiers"
    fi
    
    res=$(echo "$success_percentage < 50" | bc -l 2>/dev/null || echo 0)
    if [ "$res" -eq 1 ]; then
        echo "  • Verify broadcast domain configuration"
        echo "  • Check network connectivity between machines"
    fi
    
    res=$(echo "$amplification_factor < 1" | bc -l 2>/dev/null || echo 0)
    if [ "$res" -eq 1 ]; then
        echo "  • Verify victim is receiving packets"
        echo "  • Check IP forwarding and routing"
    fi
    
    echo "=================================="
    
    # Save results to file
    echo "Saving results to attack_results.log..."
    {
        echo "=========================================="
        echo "SMURF ATTACK SUCCESS MEASUREMENT"
        echo "Date: $(date)"
        echo "Duration: ${duration}s, Rate: ${rate} pps"
        echo "Expected Packets: $expected_packets"
        echo "Victim Received: $victim_packets"
        echo "Amplification: ${amplification_factor}x"
        echo "Success Rate: ${success_percentage}%"
        echo "Participating Amplifiers: $responding_amps/2"
        echo "Rating: $rating"
        echo "=========================================="
    } >> attack_results.log
    
    echo -e "${GREEN}Attack measurement completed!${NC}"
    echo "Results saved to attack_results.log"
}

analyze_last_attack() {
    echo -e "${YELLOW}Analyzing Last Attack Results...${NC}"
    
    if [ ! -f "attack_results.log" ]; then
        echo -e "${RED}No attack results found. Run 'measure' command first.${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${BLUE}LAST ATTACK ANALYSIS${NC}"
    tail -n 10 attack_results.log
    
    echo ""
    echo -e "${BLUE}ATTACK HISTORY${NC}"
    echo "Recent attacks:"
    grep "Date:" attack_results.log | tail -n 5
    
    echo ""
    echo "View full log: cat attack_results.log"
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
    measure)
        print_header
        measure_attack_success
        ;;
    analyze)
        print_header
        analyze_last_attack
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
