
from operator import attrgetter

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, HANDSHAKE_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

#plot
import matplotlib.pyplot as plt
import numpy


class SimpleMonitor13(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.tempTraffic = [0] * 15
        self.tempFlow = [0] * 6
        self.linkTraffic = []	
        self.timeTick = 0	
        self.timeOut = 10

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        # if dpid == 1 or dpid == 3 or dpid == 4 or dpid == 5:
        #     self.logger.debug("add datapath %d" %dpid)
        #     self.datapaths[datapath.id] = datapath

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        # install default rule (UDP)
        for eth_dst in range(1,4):
            if dpid == 3 or dpid == 4 or dpid == 5:
                if dpid == eth_dst+2:
                    match = parser.OFPMatch(
                        eth_type=0x800,
                        eth_dst='00:00:00:00:00:0%d'%eth_dst,
                        in_port=2,
                        ip_proto=17
                    )
                    actions = [parser.OFPActionOutput(1)]
                    self.add_flow(datapath, 5, match, actions)
                else:
                    match = parser.OFPMatch(
                        eth_type=0x800,
                        eth_dst='00:00:00:00:00:0%d'%eth_dst,
                        in_port=1,
                        ip_proto=17
                    )
                    actions = [parser.OFPActionOutput(2)]
                    self.add_flow(datapath, 5, match, actions)
            elif dpid == 1 or dpid == 2:
                for in_port in range(1,4):
                    if(in_port!=eth_dst):
                        match = parser.OFPMatch(
                            eth_type=0x800,
                            eth_dst='00:00:00:00:00:0%d'%eth_dst,
                            in_port = in_port,
                            ip_proto=17
                        )
                        actions = [parser.OFPActionOutput(eth_dst)]
                        self.add_flow(datapath, 5, match, actions)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            # total traffic of switch 1 and 2
            switch = [0]*2
            switch[0] = sum(self.tempFlow[0:3])
            switch[1] = sum(self.tempFlow[3:])
            switch_max = numpy.argmax(switch)
            # total traffic of h1->h2, h1->h3, h2->h3
            trans = [0]*3
            trans[0] = self.tempFlow[0]+self.tempFlow[3]
            trans[1] = self.tempFlow[1]+self.tempFlow[4]
            trans[2] = self.tempFlow[2]+self.tempFlow[5]
            # group traffics 
            index_list = [0,1,2]
            link_max = numpy.argmax(trans)
            index_list.remove(link_max)
            link_left = trans[index_list[0]]+trans[index_list[1]]
            
            for dp in self.datapaths:
                parser = dp.ofproto_parser
                if dp.id == 3:
                    if(link_max == 0 and trans[link_max]>link_left) or (link_max!=0 and trans[link_max]<=link_left):
                        match = parser.OFPMatch(
                            eth_type=0x800,
                            eth_dst='00:00:00:00:00:02',
                            in_port=1,
                            ip_proto=17
                        ) 
                        actions = [parser.OFPActionOutput(2-switch_max)]
                        self.add_flow(dp, 5, match, actions)
                    else:
                        match = parser.OFPMatch(
                            eth_type=0x800,
                            eth_dst='00:00:00:00:00:02',
                            in_port=1,
                            ip_proto=17
                        ) 
                        actions = [parser.OFPActionOutput(switch_max+1)]
                        self.add_flow(dp, 5, match, actions)

                    if(link_max == 1 and trans[link_max]>link_left) or (link_max!=1 and trans[link_max]<=link_left):
                        match = parser.OFPMatch(
                            eth_type=0x800,
                            eth_dst='00:00:00:00:00:03',
                            in_port=1,
                            ip_proto=17
                        ) 
                        actions = [parser.OFPActionOutput(2-switch_max)]
                        self.add_flow(dp, 5, match, actions)
                    else:
                        match = parser.OFPMatch(
                            eth_type=0x800,
                            eth_dst='00:00:00:00:00:03',
                            in_port=1,
                            ip_proto=17
                        ) 
                        actions = [parser.OFPActionOutput(switch_max+1)]
                        self.add_flow(dp, 5, match, actions)

                elif dp.id == 4:
                    if(link_max == 2 and trans[link_max]>link_left) or (link_max!=2 and trans[link_max]<=link_left):
                        match = parser.OFPMatch(
                            eth_type=0x800,
                            eth_dst='00:00:00:00:00:03',
                            in_port=1,
                            ip_proto=17
                        ) 
                        actions = [parser.OFPActionOutput(2-switch_max)]
                        self.add_flow(dp, 5, match, actions)
                    else:
                        match = parser.OFPMatch(
                            eth_type=0x800,
                            eth_dst='00:00:00:00:00:03',
                            in_port=1,
                            ip_proto=17
                        ) 
                        actions = [parser.OFPActionOutput(switch_max+1)]
                        self.add_flow(dp, 5, match, actions)

            




            self.linkTraffic.append(self.tempTraffic)
            self.tempTraffic = [0] * 15
            for dp in self.datapaths.values():
                self._request_stats(dp)

        #chihchien
            self.timeTick = self.timeTick + 10
            self.logger.info("Running for %d seconds", self.timeTick)
            if self.timeTick == 60:
                #TlinkTraffic = numpy.transpose(self.linkTraffic)
                    #t = numpy.arange(0, 10 * len(TlinkTraffic), 10)
                for x in range(len(self.linkTraffic) - 1, 0, -1):
                    self.logger.info("xxxxxxxx=%d", x)
                    for y in range(len(self.linkTraffic[0])):
                        self.linkTraffic[x][y] = self.linkTraffic[x][y] - self.linkTraffic[x-1][y]
                    TlinkTraffic = numpy.transpose(self.linkTraffic)
                for linkN in range(0, len(TlinkTraffic) ):
                    t = numpy.arange(0, 10 * len(TlinkTraffic[0]), 10)
                    plt.subplot(3, 5, linkN+1)
                    plt.plot(t, TlinkTraffic[linkN])
                    self.logger.info(linkN)
                    self.logger.info(TlinkTraffic[14])
                    self.logger.info("sucks")
                plt.show()
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         '
                         'in-port  eth-dst           '
                         'out-port packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)
            if ev.msg.datapath.id <= 2:
                idx = (ev.msg.datapath.id - 1) * 3
                if stat.match['in_port'] == 1 and stat.match['eth_dst'] == '10.0.0.2':
                    idx = idx
                elif stat.match['in_port'] == 1 and stat.match['eth_dst'] == '10.0.0.3':
                    idx = idx + 1
                elif stat.match['in_port'] == 2 and stat.match['eth_dst'] == '10.0.0.3':
                    idx = idx + 2
                self.tempFlow[idx] = stat.byte_count

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)
            if stat.port_no <= 3:
                idx = (stat.port_no + (ev.msg.datapath.id - 1) * 3) - 1
                self.tempTraffic[idx] += stat.rx_bytes









