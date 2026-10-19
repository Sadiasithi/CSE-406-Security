#!/usr/bin/env python3
"""
ICMP Smurf Attack Monitoring and Success Measurement Tool
Measures attack effectiveness and amplification factors
"""

import subprocess
import time
import re
import json
import threading
from datetime import datetime
import argparse

class SmurfAttackMonitor:
    """Monitor and analyze ICMP Smurf attack effectiveness"""
    
    def __init__(self, victim_ip, attacker_ip, broadcast_ip, amplifier_ips):
        self.victim_ip = victim_ip
        self.attacker_ip = attacker_ip
        self.broadcast_ip = broadcast_ip
        self.amplifier_ips = amplifier_ips
        
        # Monitoring data
        self.monitoring_active = False
        self.start_time = None
        self.end_time = None
        
        # Traffic counters
        self.victim_icmp_received = 0
        self.attack_packets_sent = 0
        self.amplifier_responses = {}
        self.total_responses = 0
        
        # Performance metrics
        self.peak_pps = 0
        self.avg_pps = 0
        self.bandwidth_peak = 0
        self.bandwidth_avg = 0
        
        print(f"[+] Attack Monitor initialized")
        print(f"    Victim: {self.victim_ip}")
        print(f"    Attacker: {self.attacker_ip}")
        print(f"    Broadcast: {self.broadcast_ip}")
        print(f"    Amplifiers: {len(self.amplifier_ips)} nodes")

    def count_amplifier_responses(self, interface="eth0", duration=60):
        """Monitor amplifier responses using tcpdump"""
        print(f"[+] Starting amplifier response monitoring for {duration}s...")
        
        # Monitor ICMP traffic to victim
        cmd = [
            "timeout", str(duration),
            "tcpdump", "-i", interface, "-n", "-c", "1000",
            f"icmp and dst {self.victim_ip}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration+5)
            
            # Parse tcpdump output
            lines = result.stdout.split('\n')
            responses_per_amplifier = {}
            total_packets = 0
            
            for line in lines:
                if "ICMP echo reply" in line:
                    # Extract source IP from tcpdump line
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+) >', line)
                    if match:
                        src_ip = match.group(1)
                        if src_ip in self.amplifier_ips:
                            responses_per_amplifier[src_ip] = responses_per_amplifier.get(src_ip, 0) + 1
                            total_packets += 1
            
            self.amplifier_responses = responses_per_amplifier
            self.total_responses = total_packets
            
            print(f"[+] Captured {total_packets} ICMP responses")
            for amp_ip, count in responses_per_amplifier.items():
                print(f"    {amp_ip}: {count} responses")
                
        except subprocess.TimeoutExpired:
            print("[!] Monitoring timeout reached")
        except Exception as e:
            print(f"[-] Error monitoring responses: {e}")

    def monitor_victim_traffic(self, interface="eth0", duration=60):
        """Monitor traffic hitting the victim to measure attack impact"""
        print(f"[+] Monitoring victim traffic for {duration}s...")
        
        cmd = [
            "timeout", str(duration),
            "tcpdump", "-i", interface, "-n", "-q",
            f"dst {self.victim_ip} and icmp"
        ]
        
        packet_count = 0
        start_time = time.time()
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    packet_count += 1
                    
                    # Calculate real-time PPS
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        current_pps = packet_count / elapsed
                        self.peak_pps = max(self.peak_pps, current_pps)
                        
                        # Print periodic updates
                        if packet_count % 10 == 0:
                            print(f"[*] Packets to victim: {packet_count}, Rate: {current_pps:.1f} pps")
            
            process.wait(timeout=5)
            
        except Exception as e:
            print(f"[-] Error monitoring victim traffic: {e}")
        
        # Calculate final statistics
        total_time = time.time() - start_time
        self.victim_icmp_received = packet_count
        self.avg_pps = packet_count / total_time if total_time > 0 else 0
        
        print(f"[+] Victim received {packet_count} ICMP packets")
        print(f"[+] Average rate: {self.avg_pps:.1f} pps, Peak: {self.peak_pps:.1f} pps")

    def calculate_amplification_factor(self, attack_packets_sent):
        """Calculate the amplification factor of the attack"""
        self.attack_packets_sent = attack_packets_sent
        
        if attack_packets_sent == 0:
            return 0
        
        amplification_factor = self.total_responses / attack_packets_sent
        
        print(f"\n[+] AMPLIFICATION ANALYSIS:")
        print(f"    Attack packets sent: {attack_packets_sent}")
        print(f"    Response packets received: {self.total_responses}")
        print(f"    Amplification factor: {amplification_factor:.2f}x")
        print(f"    Theoretical max amplification: {len(self.amplifier_ips)}x")
        
        return amplification_factor

    def calculate_success_percentage(self):
        """Calculate attack success percentage based on multiple metrics"""
        
        # Metric 1: Amplifier participation rate
        responding_amplifiers = len(self.amplifier_responses)
        total_amplifiers = len(self.amplifier_ips)
        participation_rate = (responding_amplifiers / total_amplifiers * 100) if total_amplifiers > 0 else 0
        
        # Metric 2: Response efficiency
        if self.attack_packets_sent > 0:
            response_efficiency = (self.total_responses / (self.attack_packets_sent * total_amplifiers) * 100)
        else:
            response_efficiency = 0
        
        # Metric 3: Traffic amplification achieved
        if self.attack_packets_sent > 0:
            amplification_factor = self.total_responses / self.attack_packets_sent
            amplification_percentage = (amplification_factor / total_amplifiers * 100)
        else:
            amplification_percentage = 0
        
        # Metric 4: Attack packet delivery rate (if we can measure it)
        # This would require monitoring the broadcast network too
        
        # Overall success score (weighted average)
        weights = {
            'participation': 0.3,
            'efficiency': 0.4,
            'amplification': 0.3
        }
        
        overall_success = (
            participation_rate * weights['participation'] +
            response_efficiency * weights['efficiency'] +
            amplification_percentage * weights['amplification']
        )
        
        return {
            'overall_success': min(overall_success, 100.0),
            'participation_rate': participation_rate,
            'response_efficiency': response_efficiency,
            'amplification_percentage': amplification_percentage,
            'responding_amplifiers': responding_amplifiers,
            'total_amplifiers': total_amplifiers,
            'amplification_factor': amplification_factor if self.attack_packets_sent > 0 else 0
        }

    def generate_attack_report(self, attack_duration):
        """Generate comprehensive attack success report"""
        success_metrics = self.calculate_success_percentage()
        
        print("\n" + "="*70)
        print("ICMP SMURF ATTACK SUCCESS REPORT")
        print("="*70)
        print(f"Attack Duration: {attack_duration}s")
        print(f"Monitoring Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("AMPLIFICATION ANALYSIS:")
        print(f"  • Attack Packets Sent: {self.attack_packets_sent}")
        print(f"  • Response Packets Received: {self.total_responses}")
        print(f"  • Amplification Factor: {success_metrics['amplification_factor']:.2f}x")
        print(f"  • Theoretical Maximum: {success_metrics['total_amplifiers']}x")
        print()
        
        print("AMPLIFIER PARTICIPATION:")
        print(f"  • Responding Amplifiers: {success_metrics['responding_amplifiers']}/{success_metrics['total_amplifiers']}")
        print(f"  • Participation Rate: {success_metrics['participation_rate']:.1f}%")
        
        for amp_ip in self.amplifier_ips:
            responses = self.amplifier_responses.get(amp_ip, 0)
            status = "✓ ACTIVE" if responses > 0 else "✗ SILENT"
            print(f"    - {amp_ip}: {responses} responses {status}")
        print()
        
        print("ATTACK EFFECTIVENESS:")
        print(f"  • Response Efficiency: {success_metrics['response_efficiency']:.1f}%")
        print(f"  • Amplification Achievement: {success_metrics['amplification_percentage']:.1f}%")
        print(f"  • Peak Traffic Rate: {self.peak_pps:.1f} pps")
        print(f"  • Average Traffic Rate: {self.avg_pps:.1f} pps")
        print()
        
        print("OVERALL SUCCESS RATING:")
        overall = success_metrics['overall_success']
        if overall >= 80:
            rating = "HIGHLY SUCCESSFUL"
            emoji = "🔴"
        elif overall >= 60:
            rating = "MODERATELY SUCCESSFUL"
            emoji = "🟡"
        elif overall >= 30:
            rating = "PARTIALLY SUCCESSFUL"
            emoji = "🟠"
        else:
            rating = "INEFFECTIVE"
            emoji = "🟢"
            
        print(f"  {emoji} {overall:.1f}% - {rating}")
        print()
        
        print("INTERPRETATION:")
        if overall >= 80:
            print("  The Smurf attack was highly effective. Most amplifiers")
            print("  responded, creating significant traffic amplification.")
        elif overall >= 60:
            print("  The attack achieved moderate success. Some amplifiers")
            print("  responded, but there's room for improvement.")
        elif overall >= 30:
            print("  The attack had limited success. Few amplifiers responded")
            print("  or the amplification was minimal.")
        else:
            print("  The attack was largely ineffective. Amplifiers may have")
            print("  ICMP broadcast protection enabled or network issues exist.")
        
        print("\nRECOMMENDations:")
        if success_metrics['participation_rate'] < 50:
            print("  • Check amplifier ICMP broadcast settings")
            print("  • Verify broadcast address configuration")
        if success_metrics['response_efficiency'] < 70:
            print("  • Increase packet rate for better efficiency")
            print("  • Check network connectivity")
        if overall < 30:
            print("  • Verify all machines are on the same broadcast domain")
            print("  • Check firewall rules and ICMP settings")
        
        print("="*70)
        
        return success_metrics

    def run_full_monitoring(self, attack_duration=60, interface="eth0"):
        """Run complete monitoring during attack"""
        print(f"[+] Starting full attack monitoring for {attack_duration}s...")
        self.start_time = time.time()
        
        # Start monitoring victim traffic in background
        victim_thread = threading.Thread(
            target=self.monitor_victim_traffic,
            args=(interface, attack_duration)
        )
        victim_thread.start()
        
        # Monitor amplifier responses
        self.count_amplifier_responses(interface, attack_duration)
        
        # Wait for victim monitoring to complete
        victim_thread.join()
        
        self.end_time = time.time()
        
        # Generate report
        return self.generate_attack_report(attack_duration)


def main():
    parser = argparse.ArgumentParser(description="ICMP Smurf Attack Monitor")
    parser.add_argument('-v', '--victim', required=True, help='Victim IP address')
    parser.add_argument('-a', '--attacker', required=True, help='Attacker IP address')
    parser.add_argument('-b', '--broadcast', required=True, help='Broadcast IP address')
    parser.add_argument('-A', '--amplifiers', required=True, nargs='+', 
                       help='List of amplifier IP addresses')
    parser.add_argument('-d', '--duration', type=int, default=60,
                       help='Monitoring duration in seconds')
    parser.add_argument('-i', '--interface', default='eth0',
                       help='Network interface to monitor')
    parser.add_argument('-p', '--packets', type=int, 
                       help='Number of attack packets sent (for calculation)')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = SmurfAttackMonitor(
        victim_ip=args.victim,
        attacker_ip=args.attacker,
        broadcast_ip=args.broadcast,
        amplifier_ips=args.amplifiersvictim_icvictim_icmp_receivedmp_received
    )
    
    # Run monitoring
    results = monitor.run_full_monitoring(args.duration, args.interface)
    
    # If attack packets count provided, calculate amplification
    if args.packets:
        monitor.calculate_amplification_factor(args.packets)


if __name__ == "__main__":
    main()
