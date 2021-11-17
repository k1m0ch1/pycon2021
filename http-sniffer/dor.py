from scapy.all import *
from scapy.layers.http import HTTPRequest, REQUEST_HEADERS, GENERAL_HEADERS 
from colorama import init, Fore

init()

GREEN = Fore.GREEN
RED   = Fore.RED
RESET = Fore.RESET
stars = lambda n: "*" * n

def sniff_packets(iface=None):
    if iface:
        sniff(filter="port 80", prn=process_packet, iface=iface, store=False)
    else:
        sniff(filter="port 80", prn=process_packet, store=False)

def process_packet(packet):
    if packet.haslayer(HTTPRequest):        
        url = packet[HTTPRequest].Host.decode() + packet[HTTPRequest].Path.decode()
        ip = packet[IP].src
        method = packet[HTTPRequest].Method.decode()
        print(f"\n{GREEN}[+] {ip} Requested {url} with {method}{RESET}")
        # get Header
        for item in packet[HTTPRequest].fields_desc:
            value = getattr(packet[HTTPRequest], item.name)
            if value is not None:
                print(f"{item.name} = {value}")
        if show_raw and packet.haslayer(Raw) and method == "POST":  
            # if show_raw flag is enabled, has raw data, and the requested method is "POST"
            # then show raw
            print(f"\n{RED}[*] Some useful Raw data: {packet[Raw].load}{RESET}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="HTTP Packet Sniffer, this is useful when you're a man in the middle." \
                                                 + "It is suggested that you run arp spoof before you use this script, otherwise it'll sniff your personal packets")
    parser.add_argument("-i", "--iface", help="Interface to use, default is scapy's default interface")
    parser.add_argument("--show-raw", dest="show_raw", action="store_true", help="Whether to print POST raw data, such as passwords, search queries, etc.")
    args = parser.parse_args()
    iface = args.iface
    show_raw = args.show_raw
    sniff_packets(iface)
