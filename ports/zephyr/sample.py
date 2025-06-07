import socket
import errno
def ping(host, timeout=1000):
    s = None
    try:
        # Ensure the port for getaddrinfo is 0 for ICMP, or any port if the stack ignores it for raw ICMP.
        # Using 0 is conventional for "any port" or when port is irrelevant for the protocol.
        addr_info = socket.getaddrinfo(host, 0, socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        addr = addr_info[0][-1]
        
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        s.settimeout(timeout / 1000.0) # Ensure float division for timeout

        # ICMP Echo Request: Type=8, Code=0
        # Checksum (bytes 2 and 3) set to 0x0000 for the stack to calculate
        # Identifier and Sequence Number can be simple
        identifier = 0x1234 
        sequence_number = 0x0001
        
        # Pack identifier and sequence number (ensure correct byte order - typically network byte order/big-endian)
        import ustruct
        header = bytearray(b'\x08\x00\x00\x00') # Type, Code, Checksum (0)
        header.extend(ustruct.pack('>HH', identifier, sequence_number)) # ID, Seq
        # Optional: add some payload data
        # payload = b"Hello Zephyr Ping"
        # packet = bytes(header) + payload
        packet = bytes(header)

        # If the stack doesn't calculate checksum for raw sockets, you'd need to do it here.
        # For now, assume the stack does it if checksum is 0.
        # If not, a manual checksum function would be:
        # def calculate_checksum(data):
        #     s = 0
        #     n = len(data) % 2
        #     for i in range(0, len(data)-n, 2):
        #         s += data[i] + (data[i+1] << 8)
        #     if n:
        #         s += data[len(data)-1]
        #     while (s >> 16):
        #         s = (s & 0xFFFF) + (s >> 16)
        #     s = ~s & 0xffff
        #     return s
        # chksum = calculate_checksum(packet) # Calculate over packet with checksum field as 0
        # packet = packet[0:2] + ustruct.pack('>H', chksum) + packet[4:]

        s.sendto(packet, addr)
        reply, sender_addr = s.recvfrom(1024) # Use recvfrom to get sender's address

        # Basic validation: IP header is typically 20 bytes. ICMP starts after that.
        # ICMP Echo Reply type is 0.
        ip_header_length = (reply[0] & 0x0F) * 4
        icmp_type = reply[ip_header_length]
        icmp_code = reply[ip_header_length + 1]
        # Further checks for identifier and sequence number can be added from reply[ip_header_length+4:]

        if icmp_type == 0 and icmp_code == 0: # Echo Reply
            print("Ping successful to {} ({})".format(host, addr[0]))
        else:
            print("Ping received from {} ({}), but not an echo reply (Type={}, Code={})".format(host, addr[0], icmp_type, icmp_code))
            
    except OSError as e:
        err_num = e.args[0] if e.args else "unknown"
        # Assuming errno_to_str is defined as in your example
        err_name = errno_to_str(err_num) if callable(globals().get("errno_to_str")) else str(err_num)
        print("Ping failed to {}: {} ({})".format(host, err_num, err_name))
    except Exception as e: # Catch other potential errors like getaddrinfo failures not raising OSError
        print("Ping failed to {}: {}".format(host, e))
    finally:
        if s is not None:
            s.close()

# Helper function to convert errno to string if available
def errno_to_str(err):
    for name in dir(errno):
        if name.startswith("E") and getattr(errno, name) == err:
            return name
    return "UNKNOWN"
