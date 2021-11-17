from scapy.all import *
import zlib
import uuid
import re
import sys

#Usage Instructions
def usage():
    print("\n")
    print(f"Strip URL Usage (with pcap file): python3 {sys.argv[0]} --inputpcap /path/to/pcap --stripurl /path/to/file")
    print(f"Strip URL Usage (sniff mode): python3 {sys.argv[0]} --iface <interface> --stripurl /path/to/file")
    print("\n")
    print(f"Strip TXT Usage: python3 {sys.argv[0]} --inputpcap /path/to/pcap --striptxt /path/to/folder")
    print(f"Strip TXT Usage: python3 {sys.argv[0]} --iface <interface> --striptxt /path/to/folder")
    print("\n")
    print(f"Strip Image Usage: python3 {sys.argv[0]} --inputpcap /path/to/pcap --stripimg /path/to/folder")
    print("\n")
    sys.exit()

#Given the payload, try to extract the payload and write to file
def extract_payload(http_headers, payload, output_path):
    payload_type = http_headers["Content-Type"].split("/")[1].split(";")[0]
    try:
        if "Content-Encoding" in http_headers.keys():
            if http_headers["Content-Encoding"] == "gzip":
                file = zlib.decompress(payload, 16+zlib.MAX_WBITS)
            elif http_headers["Content-Encoding"] == "deflate":
                file = zlib.decompress(payload)
            else:
                file = payload
        else:
            file = payload
    except:
        pass

    filename = uuid.uuid4().hex + "." + payload_type
    file_path = output_path + "/" + filename
    fd = open(file_path, "wb")
    fd.write(file)
    fd.close()

#Given pcap and output directory, try to extract urls from HTTP GET Requests
#Write URLs to file
def stripurl_pcap(pcap, output_path):
    a = rdpcap(pcap)
    sessions = a.sessions()
    fd = open(output_path, "wb")
    for session in sessions:
        for packet in sessions[session]:
            try:
                if packet[TCP].dport == 80:
                    payload = bytes(packet[TCP].payload)
                    url_path = payload[payload.index(b"GET ")+4:payload.index(b" HTTP/1.1")].decode("utf8")
                    http_header_raw = payload[:payload.index(b"\r\n\r\n")+2]
                    http_header_parsed = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", http_header_raw.decode("utf8")))
                    url = http_header_parsed["Host"] + url_path + "\n"
                    fd.write(url.encode())
            except:
                pass
    fd.close()
    sys.exit(0)

#Given pcap and output directory, try to extract images from HTTP Responses
#Write images to output directory
def stripimg_pcap(pcap, output_path):
    a = rdpcap(pcap)
    sessions = a.sessions()
    for session in sessions:
        http_payload = b""
        for packet in sessions[session]:
            try:
                if packet[TCP].sport == 80:
                    payload = bytes(packet[TCP].payload)
                    http_header_exists = False
                    try:
                        http_header = payload[payload.index(b"HTTP/1.1"):payload.index(b"\r\n\r\n")+2]
                        if http_header:
                            http_header_exists = True
                    except:
                        pass
                    if not http_header_exists and http_payload:
                        http_payload += payload
                    elif http_header_exists and http_payload:
                        http_header_raw = http_payload[:http_payload.index(b"\r\n\r\n")+2]
                        http_header_parsed = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", http_header_raw.decode("utf8")))
                        if "Content-Type" in http_header_parsed.keys():
                            if "image" in http_header_parsed["Content-Type"]:
                                image_payload = http_payload[http_payload.index(b"\r\n\r\n")+4:]
                                if image_payload:
                                    extract_payload(http_header_parsed, image_payload, output_path)
                        http_payload = payload
                    elif http_header_exists and not http_payload:
                        http_payload = payload
            except:
                pass
    sys.exit(0)

#Given pcap and output directory, try to extract text payloads from HTTP Responses
#Write text payloads to output directory
def striptxt_pcap(pcap, output_path):
    a = rdpcap(pcap)
    sessions = a.sessions()
    for session in sessions:
        http_payload = b""
        for packet in sessions[session]:
            try:
                if packet[TCP].sport == 80:
                    payload = bytes(packet[TCP].payload)
                    http_header_exists = False
                    try:
                        http_header = payload[payload.index(b"HTTP/1.1"):payload.index(b"\r\n\r\n")+2]
                        if http_header:
                            http_header_exists = True
                    except:
                        pass
                    if http_header_exists:
                        http_header_raw = payload[:payload.index(b"\r\n\r\n")+2]
                        http_header_parsed = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", http_header_raw.decode("utf8")))
                        if "Content-Type" in http_header_parsed.keys():
                            if "text" in http_header_parsed["Content-Type"]:
                                txt_payload = payload[payload.index(b"\r\n\r\n")+4:]
                                if txt_payload:
                                    extract_payload(http_header_parsed, txt_payload, output_path)
            except:
                pass
    sys.exit(0)

#Given an interface to sniff, try to extract urls on the fly and write to file
def stripurl_sniff(iface, output_path):

    def stripurl_packet(packet):
        try:
            if packet[TCP].dport == 80:
                payload = bytes(packet[TCP].payload)
                url_path = payload[payload.index(b"GET ")+4:payload.index(b" HTTP/1.1")].decode("utf8")
                http_header_raw = payload[:payload.index(b"\r\n\r\n")+2]
                http_header_parsed = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", http_header_raw.decode("utf8")))
                url = http_header_parsed["Host"] + url_path + "\n"
                fd.write(url.encode())
        except:
            pass

    conf.iface = iface
    fd = open(output_path, "wb")
    try:
        print(f"[*] Stripping URLs => {output_path}. CTRL-C to cancel")
        sniff(iface=conf.iface, prn=stripurl_packet,store=0)
    except KeyboardInterrupt:
        print(f"[*] Exiting")
        fd.close()
        sys.exit(0)

#Given an interface to sniff, try to extract text payloads on the fly and write to file
def striptxt_sniff(iface, output_path):

    def striptxt_packet(packet):
        try:
            if packet[TCP].sport == 80:
                payload = bytes(packet[TCP].payload)
                http_header_exists = False
                try:
                    http_header = payload[payload.index(b"HTTP/1.1"):payload.index(b"\r\n\r\n")+2]
                    if http_header:
                        http_header_exists = True
                except:
                    pass
                if http_header_exists:
                    http_header_raw = payload[:payload.index(b"\r\n\r\n")+2]
                    http_header_parsed = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", http_header_raw.decode("utf8")))
                    if "Content-Type" in http_header_parsed.keys():
                        if "text" in http_header_parsed["Content-Type"]:
                            txt_payload = payload[payload.index(b"\r\n\r\n")+4:]
                            if txt_payload:
                                extract_payload(http_header_parsed, txt_payload, output_path)
        except:
            pass

    conf.iface = iface
    try:
        print(f"[*] Stripping TXT => {output_path}. CTRL-C to cancel")
        sniff(iface=conf.iface, prn=striptxt_packet, store=0)
    except KeyboardInterrupt:
        print(f"[*] Exiting")
        sys.exit(0)

#Check cmd line arguments
def start_script(arguments):
    if len(arguments) == 5:
        if arguments[1] == "--inputpcap" and arguments[3] == "--stripurl":
            stripurl_pcap(arguments[2], arguments[4])
        elif arguments[1] == "--inputpcap" and arguments[3] == "--stripimg":
            stripimg_pcap(arguments[2], arguments[4])
        elif arguments[1] == "--inputpcap" and arguments[3] == "--striptxt":
            striptxt_pcap(arguments[2], arguments[4])
        elif arguments[1] == "--iface" and arguments[3] == "--stripurl":
            stripurl_sniff(arguments[2], arguments[4])
        elif arguments[1] == "--iface" and arguments[3] == "--striptxt":
            striptxt_sniff(arguments[2], arguments[4])
        else:
            usage()
    else:
        usage()

#Start the script
start_script(sys.argv)
