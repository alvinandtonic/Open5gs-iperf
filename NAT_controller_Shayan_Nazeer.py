import logging
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.packet import packet, ipv4, tcp, udp, icmp
from ryu.controller import dpset
from netaddr import IPNetwork
from collections import namedtuple


class NAT(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NAT, self).__init__(*args, **kwargs)
        global ex_ip
        global maps
        global ports
        ex_ip = "128.128.129.1"
        maps = {}
        ports = list(range(5000, 60000))
        self.Ipv4_addr = namedtuple("Ipv4_addr", ["addr", "port"])

    def add_flow(self, datapath, match, actions, priority=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            actions=actions,
            hard_timeout=hard_timeout,
            cookie=0,
            command=ofproto.OFPFC_ADD,
        )
        datapath.send_msg(mod)
        self.logger.debug("add_flow:" + str(mod))

    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def _event_switch_enter_handler(self, ev):
        dl_type_arp = 0x0806
        dl_type_ipv4 = 0x0800
        dl_type_ipv6 = 0x86DD
        dp = ev.dp
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        self.logger.info("switch connected %s", dp)

        # pass packet directly
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]

        # arp
        match = parser.OFPMatch(dl_type=dl_type_arp)
        self.add_flow(dp, match, actions)

        # ipv6
        match = parser.OFPMatch(dl_type=dl_type_ipv6)
        self.add_flow(dp, match, actions)

        # igmp
        match = parser.OFPMatch(dl_type=dl_type_ipv4, nw_proto=2)
        self.add_flow(dp, match, actions)

        # do address translation for following types of packet
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]

        # icmp
        match = parser.OFPMatch(dl_type=dl_type_ipv4, nw_proto=1)
        self.add_flow(dp, match, actions)

        # tcp
        match = parser.OFPMatch(dl_type=dl_type_ipv4, nw_proto=6)
        self.add_flow(dp, match, actions)

        # udp
        match = parser.OFPMatch(dl_type=dl_type_ipv4, nw_proto=17)
        self.add_flow(dp, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        self.logger.info("msg in")
        message = ev.msg
        self.logger.info("message %s", message)
        datapath = message.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt = packet.Packet(message.data)
        ip = pkt.get_protocol(ipv4.ipv4)

        bitmask = "24"
        src_match = IPNetwork("192.168.0.0/" + bitmask)
        dst_match = ex_ip

        if message.in_port == ofproto.OFPP_LOCAL:
            out_port = 1
        else:
            out_port = ofproto.OFPP_LOCAL

        # TCP/UDP
        if ip.proto in [17, 6]:
            t = pkt.get_protocol(tcp.tcp)
            self.logger.info("tcp %s", t)
            u = pkt.get_protocol(udp.udp)

            if IPNetwork(ip.src + "/" + bitmask) == src_match:
                src_port = t.src_port if t else u.src_port
                ip_addr = self.Ipv4_addr(addr=ip.src, port=src_port)

                # Map Client Source Address and Port to External IP and Port
                if ip_addr in maps:
                    port = maps[ip_addr]
                else:
                    port = ports.pop()
                    maps[ip_addr] = port
                    maps[port] = ip_addr
                print(f"Created Mapping: {ip_addr} {ip_addr.port} to {ex_ip} {port}")
                actions = [
                    parser.OFPActionSetNwSrc(self.ipv4_to_int(ex_ip)),
                    parser.OFPActionSetTpSrc(port),
                    parser.OFPActionOutput(out_port),
                ]

                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=message.buffer_id,
                    data=message.data,
                    in_port=message.in_port,
                    actions=actions,
                )
                datapath.send_msg(out)
                print("Packet Sent")
                return
            elif ip.dst == dst_match:
                dst_port = t.dst_port if t else u.dst_port
                print(f"dst_port: {dst_port}")

                if dst_port in maps:
                    ip_addr = maps[dst_port]
                    print(f"dst port: {dst_port}")
                else:
                    print("Dropping msg as dst is not understood")
                    return
                actions = [
                    parser.OFPActionSetNwDst(self.ipv4_to_int(ip_addr.addr)),
                    parser.OFPActionSetTpDst(ip_addr.port),
                    parser.OFPActionOutput(out_port),
                ]
                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=message.buffer_id,
                    data=message.data,
                    in_port=message.in_port,
                    actions=actions,
                )
                datapath.send_msg(out)
                print("Packet Sent")
                return
        else:
            actions = [parser.OFPActionOutput(out_port)]
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=message.buffer_id,
                data=message.data,
                in_port=message.in_port,
                actions=actions,
            )
            datapath.send_msg(out)

    def ipv4_to_str(self, integer):
        ip_list = [str((integer >> (24 - (n * 8)) & 255)) for n in range(4)]
        return ".".join(ip_list)

    def ipv4_to_int(self, string):
        ip = string.split(".")
        assert len(ip) == 4
        i = 0
        for b in ip:
            b = int(b)
            i = (i << 8) | b
        return i
