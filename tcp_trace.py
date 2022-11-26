from __future__ import print_function
from bcc import BPF
import socket
from bcc.utils import printb
import sys

def ntoa(addr):
    # IPv4アドレスを32bitにパックしたバイナリ形式に変換し、長さ4の文字列として返す。
    packed_ip_addr = socket.inet_aton(str(addr)) 
    # 32bitにパックしたバイナリ形式のIPv4アドレスをドット記法による文字列(‘127.0.0.1’など)に変換する。
    unpacked_ip_addr = socket.inet_ntoa(packed_ip_addr)
    return unpacked_ip_addr.encode('utf-8')

def print_event(cpu, data, size):
    event = bpf["events"].event(data)
    printb(b"%-6d %-16s %-16s %-16s %-16d" % (event.pid, event.comm, ntoa(event.saddr), ntoa(event.daddr), event.dport))
    
    
bpf = BPF(src_file = "trace.c")
bpf.attach_kprobe(event = "tcp_v4_connect", fn_name = "tcp_connect")
bpf.attach_kretprobe(event = "tcp_v4_connect", fn_name = "tcp_connect_ret")
bpf["events"].open_perf_buffer(print_event)

print("%-6s %-16s %-16s %-16s %-16s" % ("PID", "COMMAND", "SOURCE-IPADDR", "DESTINATIOM-IPADDR", "DPORT"))
while 1:
    bpf.perf_buffer_poll()