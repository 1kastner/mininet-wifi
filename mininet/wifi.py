"""
wifi setups to Mininet-WiFi.

author: Ramon Fontes (ramonrf@dca.fee.unicamp.br)

"""

import os
import socket
import struct
import fcntl
import fileinput
import subprocess
import glob
import math

import numpy as np
import scipy.spatial.distance as distance 
import matplotlib.patches as patches
import matplotlib.pyplot as plt
        
from mininet.mobility import gauss_markov, \
    truncated_levy_walk, random_direction, random_waypoint, random_walk

class checkNM ( object ):
    """ add mac address inside of /etc/NetworkManager/NetworkManager.conf """
    @classmethod 
    def checkNetworkManager(self, storeMacAddress): 
        self.storeMacAddress = storeMacAddress     
        self.printMac = False   
        unmatch = ""
        if(os.path.exists('/etc/NetworkManager/NetworkManager.conf')):
            if(os.path.isfile('/etc/NetworkManager/NetworkManager.conf')):
                self.resultIface = open('/etc/NetworkManager/NetworkManager.conf')
                lines=self.resultIface
        
            isNew=True
            for n in lines:
                if("unmanaged-devices" in n):
                    unmatch = n
                    echo = n
                    echo.replace(" ", "")
                    echo = echo[:-1]+";"
                    isNew = False
            if(isNew):
                os.system("echo '#' >> /etc/NetworkManager/NetworkManager.conf")
                unmatch = "#"
                echo = "[keyfile]\nunmanaged-devices="
            
            for n in range(len(self.storeMacAddress)): 
                if self.storeMacAddress[n] not in unmatch:
                    echo = echo + "mac:"
                    echo = echo + self.storeMacAddress[n] + ";"
                    self.printMac = True
                
            if(self.printMac):
                for line in fileinput.input('/etc/NetworkManager/NetworkManager.conf', inplace=1): 
                    if(isNew):
                        if line.__contains__('#'): 
                            print line.replace(unmatch, echo)
                        else:
                            print line.rstrip()
                    else:
                        if line.__contains__('unmanaged-devices'): 
                            print line.replace(unmatch, echo)
                        else:
                            print line.rstrip()
             
    @classmethod 
    def getMacAddress(self, ap):
        """ get Mac Address of any Interface """
        self.storeMacAddress=[]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', '%s'[:15]) % str(ap.virtualWlan))
        self.storeMacAddress.append(''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1])
        self.checkNetworkManager(self.storeMacAddress)
    
    @classmethod   
    def APfile(self, cmd, ap):
        """ run an Access Point and create the config file  """
        apcommand = cmd + ("\' > %s.conf" % ap.virtualWlan)  
        os.system(apcommand)
        cmd = ("hostapd -B %s.conf" % ap.virtualWlan)
        subprocess.check_output(cmd, shell=True)
        #os.system(cmd)

class getWlan( object ):
    
    @classmethod    
    def physical(self):
        self.phyInterfaces = []        
        self.phyInterfaces = (subprocess.check_output("iwconfig 2>&1 | grep IEEE | awk '{print $1}'",
                                                      shell=True)).split('\n')
        self.phyInterfaces.pop()
        return self.phyInterfaces
    
    @classmethod    
    def virtual(self):
        self.newapif=[]
        self.apif = subprocess.check_output("iwconfig 2>&1 | grep IEEE | awk '{print $1}'",
                                            shell=True).split('\n')
        for apif in self.apif:
            if apif not in module.physicalWlan and apif!="":
                self.newapif.append(apif)
        self.newapif = sorted(self.newapif)
        self.newapif.sort(key=len, reverse=False)
        return self.newapif

class module( object ):
    """ Starts and Stop the module """            
    wifiRadios = 0
    isWiFi = False
    physicalWlan = []
    isCode = False
    virtualWlan = []
        
    @classmethod    
    def _start_module(self, wifiRadios):
        """ Start wireless Module """
        os.system( 'modprobe mac80211_hwsim radios=%s' % wifiRadios )
     
    @classmethod
    def _stop_module(self):
        """ Stop wireless Module """   
        if glob.glob("*.conf"):
            os.system( 'rm *.conf' )
        
        if glob.glob("*.txt"):
            os.system( 'rm *.txt' )
       
        os.system( 'rmmod mac80211_hwsim' )
        if accessPoint.exists:
            os.system( 'killall -9 hostapd' )
        
    @classmethod
    def startEnvironment(self):
        self.physicalWlan = getWlan.physical()  #Get Phisical Wlan(s)
        self.isWiFi=True
        self._start_module(module.wifiRadios) #Initatilize WiFi Module
        phyInt.totalPhy = phyInt.getPhy() #Get Phy Interfaces                    
        
class association( object ):
    
    @classmethod    
    def setAdhocParameters(self, sta, iface, mode):
        """ Set wifi AdHoc Parameters. Have to use models for loss, latency, bw... """
        self.mode = mode
        latency = 10
        #delay = 5 * distance
        bandwidth = wifiParameters.set_bw(mode)
        sta.cmd("tc qdisc add dev %s-%s root tbf rate %smbit latency %sms burst 1540" % 
                      (str(sta), iface, bandwidth, latency)) 

    @classmethod    
    def parameters(self, sta, ap, distance, wlan):
        """ Wifi Parameters """
        seconds = 3
        try:
            """Based on RandomPropagationDelayModel (ns3)"""
            seconds = abs(mobility.speed[sta])
        except:
            pass
        
        latency = wifiParameters.latency(distance)
        loss = wifiParameters.loss(distance, sta.mode)
        delay = wifiParameters.delay(distance, seconds)
        bw = wifiParameters.bw(distance, sta.mode)  
        
        sta.pexec("tc qdisc replace dev %s-wlan%s \
            root netem rate %.2fmbit \
            loss %.1f%% \
            latency %.2fms \
            delay %.2fms" % (sta, wlan, bw, loss, latency, delay)) 
        
        if str(ap) == sta.ifaceAssociatedToAp[wlan]:
            associated = self.doAssociation(sta.mode, distance) 
        else:
            aps = 0
            for n in range(0,len(sta.ifaceAssociatedToAp)):
                if 'ap' in sta.ifaceAssociatedToAp[n]:
                    aps+=1
            if len(sta.ifaceAssociatedToAp) == aps:
                associated = True
            else:
                associated = False
            
       # isAssociated = station.isAssociated(sta, wlan)        
            
        #Only if is a mobility topology
        if mobility.ismobility == True: 
            changeAP = False
            mobilityReason = dict ()      
            
            """useful to llf (Least-loaded-first)"""
            if mobility.leastLoadFirst == True:
                llf = False
                for ap in accessPoint.name:
                    if str(ap) == sta.ifaceAssociatedToAp[wlan]:
                        accessPoint.numberOfAssociatedStations(str(ap))
                        ref_llf = accessPoint.nAssociatedStations[str(ap)]
                        llf = True
            
                if llf == True:
                    accessPoint.numberOfAssociatedStations(ap)
                    if accessPoint.nAssociatedStations[ap]+2 < ref_llf:
                        mobilityReason.setdefault( 'reason', 'llf' )
                        changeAP = True
            
            """useful to ssf (Strongest-signal-first)"""
            if accessPoint.manual_apRange!=-10:
                for ap in accessPoint.name:
                    if str(ap) == sta.ifaceAssociatedToAp[wlan]:
                        ref_Distance = mobility.getDistance(sta,ap)
                        if ref_Distance > accessPoint.manual_apRange:
                            changeAP = True
                if distance <= accessPoint.manual_apRange and changeAP == True: 
                    mobilityReason.setdefault( 'reason', 'ssf' )
                    changeAP = True
                else:
                    changeAP = False
                    
            #Go to handover    
            if associated == False or changeAP == True:
                mobility.handover(sta, ap, wlan, distance, changeAP, **mobilityReason)

                    
    @classmethod    
    def setInfraParameters(self, sta, ap, distance, wlan):
        """ Set wifi Infrastrucure Parameters. Have to use models for loss, latency, bw.."""
        if wlan != '':
            self.parameters(sta, ap, distance, wlan)
        else:
            for wlan in range(int(station.wlans[str(sta)])):
                self.parameters(sta, ap, distance, wlan)
            
    @classmethod    
    def doAssociation(self, mode, distance):
        """ Associate/Disassociate according the distance """
        associate = True
        if (distance > wifiParameters.get_range(mode)):
            associate = False
        return associate
            
class phyInt ( object ):
    
    phy = {}
    totalPhy = []
    
    @classmethod
    def getPhy(self):
        """ Get phy """ 
        phy = subprocess.check_output("find /sys/kernel/debug/ieee80211 -name hwsim | cut -d/ -f 6 | sort", 
                                                             shell=True).split("\n")
        phy.pop()
        return phy
        
class station ( object ):
    
    doAssociation = {}
    addressingSta = {}
    wlans = {}
    indexStaIface = {}
    nextIface = {}  
    printCon = True  
    fixedPosition = []
    apIface = []
    
    @classmethod    
    def ifconfig(self, sta):
        try: 
            self.addressingSta[sta]+=1
        except:
            self.addressingSta[sta] = 0
        return self.addressingSta[sta]  
     
    @classmethod    
    def assingIface(self, stations):
        wlan = getWlan.virtual()
        for i, sta in enumerate(stations):
            if 'sta' in str(stations[i]):
                for j in range(0,int(self.wlans[str(stations[i])])):
                    sta = stations[i]
                    vwlan = module.virtualWlan.index(str(sta))
                    os.system('iw phy %s set netns %s' % ( phyInt.totalPhy[vwlan + j], sta.pid ))
                    sta.cmd('ip link set dev %s name %s-wlan%s' % (wlan[vwlan + j], str(sta), j))   
      
    @classmethod    
    def confirmMeshAssociation(self, sta, interface):
        associated = ''
        while(associated == '' or len(associated) == 11):
            sta.sendCmd('ifconfig mp0 | grep -o \'TX b.*\' | cut -f2- -d\':\'')
            associated = sta.waitOutput()
        wifiParameters.get_frequency(sta, interface)
        wifiParameters.get_tx_power(sta, interface)    
        wifiParameters.get_rsi(sta, interface)    
    
    @classmethod    
    def confirmAdhocAssociation(self, sta, interface, ssid):
        associated = ''
        while(associated == '' or len(associated) == 0):
            sta.sendCmd("iw dev %s scan ssid | grep %s" % (interface, ssid))
            associated = sta.waitOutput()
        wifiParameters.get_frequency(sta, interface)
        wifiParameters.get_tx_power(sta, interface)
        wifiParameters.get_rsi(sta, interface)  
    
    @classmethod    
    def confirmInfraAssociation(self, sta, wlan, ap):
        associated = ''
        if self.printCon:
            print "Associating %s to %s" % (sta, ap)
        while(associated == '' or len(associated[0]) == 15):
            associated = self.isAssociated(sta, wlan)
        interface = str(sta)+'-wlan%s' % wlan
        wifiParameters.get_frequency(sta, interface)
        wifiParameters.get_tx_power(sta, interface)
        wifiParameters.get_rsi(sta, interface)   
            
    @classmethod    
    def isAssociated(self, sta, iface):
        associated = sta.pexec("iw dev %s-wlan%s link" % (sta, iface))
        return associated
            
    @classmethod    
    def associate(self, sta, ap):
        """ Associate to an Access Point """ 
        sta.ifaceToAssociate += 1
        wlan = sta.ifaceToAssociate
        self.cmd_associate(sta, wlan, ap)        
        
    @classmethod    
    def cmd_associate(self, sta, wlan, ap):
        sta.associatedAp = ap
        sta.cmd("iw dev %s-wlan%s connect %s" % (sta, wlan, ap.ssid))
        self.confirmInfraAssociation(sta, wlan, ap)
        sta.ifaceAssociatedToAp[wlan] = str(ap) 
        
    @classmethod    
    def adhoc(self, sta, ssid=None, mode=None, **params):
        """ Adhoc mode """   
        sta.ifaceToAssociate += 1
        iface = sta.ifaceToAssociate
        self.ssid = ssid
        self.mode = mode
        association.setAdhocParameters(sta, iface, mode)
        sta.cmd("iw dev %s-wlan%s set type ibss" % (str(sta), iface))
        sta.cmd("iw dev %s-wlan%s ibss join %s 2412" % (str(sta), iface, self.ssid))
        print "associating %s ..." % str(sta)
        interface = '%s-wlan%s' % (str(sta), iface)
        self.confirmAdhocAssociation(sta, interface, self.ssid)
        
    @classmethod    
    def addMesh(self, sta, ssid=None, mode=None, channel=None, 
                ipaddress=None, **params):
        """ Mesh mode """   
        sta.ifaceToAssociate += 1
        iface = sta.ifaceToAssociate
        self.ssid = ssid
        self.mode = mode
        self.host = sta
        sta.cmd('iw dev %s-wlan%s interface add mp0 type mp' % (str(sta), iface))
        sta.cmd('iw dev mp0 set %s' % channel)
        sta.cmd('ifconfig mp0 192.168.10.%s up' % ipaddress)
        sta.cmd('iw dev mp0 mesh join %s' % ssid)
        association.setAdhocParameters(self.host, iface, mode)
        print "associating %s ..." % str(sta)
        interface = '%s-wlan%s' % (str(sta), iface)
        self.confirmMeshAssociation(self.host, interface)        
            
class accessPoint ( object ):    

    name = []
    number = 0
    exists = False   
    manual_apRange = -10   
    nAssociatedStations = {}
    
    @classmethod
    def wds(self, ap1, int1, ap2, int2):
        os.system('iw dev %s set 4addr off' % int1)
        os.system('iw dev %s interface add wds.%s type managed 4addr on' % (int1, int1))
        os.system('iw dev %s set 4addr off' % int2)
        os.system('iw dev %s interface add wds.%s type managed 4addr on' % (int2, int2))
        os.system('ifconfig wds.%s down' % int1)
        os.system('ifconfig wds.%s down' % int2)
        os.system('ip link set dev wds.wlan2 addr 02:00:00:00:00:00')
        os.system('ip link set dev wds.wlan1 addr 02:00:00:00:01:00')
        os.system('ifconfig wds.%s up' % int1)
        os.system('ifconfig wds.%s up' % int2)
        
    @classmethod
    def rename( self, intf, newname ):
        "Rename interface"
        os.system('ifconfig %s down' % intf)
        os.system('ip link set %s name %s' % (intf, newname))
        os.system('ifconfig %s up' % newname)
        return newname
    
    @classmethod
    def numberOfAssociatedStations( self, ap ):
        "Number of Associated Stations"
        cmd = 'iw dev %s-wlan0 station dump | grep Sta | grep -c ^' % ap     
        proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)   
        (out, err) = proc.communicate()
        output = out.rstrip('\n')
        self.nAssociatedStations[ap] = int(output)
    
    @classmethod
    def start(self, ap, country_code=None, auth_algs=None, wpa=None, 
              wpa_key_mgmt=None, rsn_pairwise=None, wpa_passphrase=None, **params):
        """ Starts an Access Point """
        self.exists = True
        self.cmd = ("echo \'")
        """General Configurations"""             
        self.cmd = self.cmd + ("interface=%s" % ap.virtualWlan) # the interface used by the AP
        """Not using at the moment"""
        self.cmd = self.cmd + ("\ndriver=nl80211")
        self.cmd = self.cmd + ("\nssid=%s" % ap.ssid) # the name of the AP
        self.cmd = self.cmd + ("\nhw_mode=%s" % ap.mode) 
        self.cmd = self.cmd + ("\nchannel=%s" % ap.channel) # the channel to use 
        if(ap.mode=="ac"):
            self.cmd = self.cmd + ("\nwme_enabled=1") 
            self.cmd = self.cmd + ("\nieee80211ac=1")
        self.cmd = self.cmd + ("\nwme_enabled=1") 
        #self.cmd = self.cmd + ("\nieee80211n=1")
        if(ap.mode=="n"):
            self.cmd = self.cmd + ("\nht_capab=[HT40+][SHORT-GI-40][DSSS_CCK-40]")
        
        #Not used yet!
        if(country_code!=None):
            self.cmd = self.cmd + ("\ncountry_code=%s" % country_code) # the country code
        if(auth_algs!=None):
            self.cmd = self.cmd + ("\nauth_algs=%s" % auth_algs) # 1=wpa, 2=wep, 3=both
        if(wpa!=None):
            self.cmd = self.cmd + ("\nwpa=%s" % wpa) # WPA2 only
        if(wpa_key_mgmt!=None):
            self.cmd = self.cmd + ("\nwpa_key_mgmt=%s" % wpa_key_mgmt ) 
        if(rsn_pairwise!=None):
            self.cmd = self.cmd + ("\nrsn_pairwise=%s" % rsn_pairwise)  
        if(wpa_passphrase!=None):
            self.cmd = self.cmd + ("\nwpa_passphrase=%s" % wpa_passphrase)                        
        
        #elif(len(self.baseStationName)>self.countAP and len(self.baseStationName) != 1):
        #    """From AP2"""
        #    self.cmd = self.apcommand
            #self.cmd = self.cmd + "\n"
        #    self.cmd = self.cmd + ("\nbss=%s" % self.newapif[self.nextIface]) # the interface used by the AP
        #    if(self.ssid!=None):
        #        self.cmd = self.cmd + ("\nssid=%s" % self.ssid ) # the name of the AP
                #self.cmd = self.cmd + ("\nssid=%s" % self.ssid) # the name of the AP
        #    if(self.auth_algs!=None):
        #        self.cmd = self.cmd + ("\nauth_algs=%s" % self.auth_algs) # 1=wpa, 2=wep, 3=both
        #    if(self.wpa!=None):
        #        self.cmd = self.cmd + ("\nwpa=%s" % self.wpa) # WPA2 only
        #    if(self.wpa_key_mgmt!=None):
        #        self.cmd = self.cmd + ("\nwpa_key_mgmt=%s" % self.wpa_key_mgmt ) 
        #    if(self.rsn_pairwise!=None):
        #        self.cmd = self.cmd + ("\nrsn_pairwise=%s" % self.rsn_pairwise)  
        #    if(self.wpa_passphrase!=None):
        #        self.cmd = self.cmd + ("\nwpa_passphrase=%s" % self.wpa_passphrase)  
        #    self.countAP = len(self.baseStationName)
        #    self.apcommand = ""        
        return self.cmd
        
    @classmethod
    def apBridge(self, ap, iface):
        """ AP Bridge """  
        intf = str(ap)+'-'+str(iface[:4])+str(0)
        os.system("ovs-vsctl add-port %s %s" % (ap, intf))
        
    @classmethod
    def setBw(self, ap):
        """ Set bw to AP """  
        bandwidth = wifiParameters.set_bw(ap.mode)
        os.system("tc qdisc add dev %s root tbf rate %smbit latency 2ms burst 15k" % \
                  (ap.virtualWlan, bandwidth))   
        
class mobility ( object ):    
    """ Mobility """          
    speed = {}
    nodePosition = {}      
    plotap = {}
    plotsta = {}
    plottxt = {}
    nodesPlotted = []
    plotGraph = False
    cancelPlot = False
    ismobility = False
    leastLoadFirst = False
    DRAW = False
    MAX_X = 50
    MAX_Y = 50
    
    @classmethod 
    def closePlot(self):
        plt.close()
    
    @classmethod   
    def range(self, mode):
        if (mode=='a'):
            self.distance = 33
        elif(mode=='b'):
            self.distance = 50
        elif(mode=='g'):
            self.distance = 33 
        elif(mode=='n'):
            self.distance = 70
        elif(mode=='ac'):
            self.distance = 100 
            
        return self.distance
    
    @classmethod   
    def move(self, node, diffTime, speed, startposition, endposition):      
        """
            Moving nodes
            diffTime: important to calculate the speed  
        """
        pos_x = float(endposition[0]) - float(startposition[0])
        pos_y = float(endposition[1]) - float(startposition[1])
        pos_z = float(endposition[2]) - float(startposition[2])
        
        self.nodePosition[node] = pos_x, pos_y, pos_z
        self.speed[node] = ((pos_x + pos_y + pos_z)/diffTime) 
        
        pos = '%.5f,%.5f,%.5f' % (pos_x/diffTime, pos_y/diffTime, pos_z/diffTime)
        pos = pos.split(',')
        return pos       
    
    @classmethod 
    def plot(self, src, dst, pos_src, pos_dst):
        MAX_X = self.MAX_X
        MAX_Y = self.MAX_Y
        
        plt.ion()
        ax = plt.subplot(111)
        
        if 'sta' in str(dst) and str(dst) not in self.nodesPlotted:
            node = str(dst)
            self.plottxt[node] = ax.annotate(node, xy=(pos_dst[0],pos_dst[1]))
            self.plotsta[node], = ax.plot(range(MAX_X), range(MAX_Y), linestyle='', marker='.', ms=12, mfc='blue')
            self.nodesPlotted.append(node)
            self.plotsta[node].set_data(pos_dst[0],pos_dst[1])
        elif 'sta' in str(src) and str(src) not in self.nodesPlotted:
            node = str(src)
            self.plottxt[node] = ax.annotate(node, xy=(pos_src[0],pos_src[1]))
            self.plotsta[node], = ax.plot(range(MAX_X), range(MAX_Y), linestyle='', marker='.', ms=12, mfc='blue')
            self.nodesPlotted.append(node)
            self.plotsta[node].set_data(pos_src[0],pos_src[1])
        
        if 'sta' in str(src):
            self.plotsta[str(src)].set_data(pos_src[0],pos_src[1])
            self.plottxt[str(src)].xytext = (pos_src[0],pos_src[1])
        elif 'sta' in str(dst):
            self.plotsta[str(dst)].set_data(pos_dst[0],pos_dst[1])
            self.plottxt[str(dst)].xytext = (pos_dst[0],pos_dst[1])
        
        if 'ap' in str(dst) and str(dst) not in self.nodesPlotted:
            ap = dst
            pos_0 = pos_dst[0]
            pos_1 = pos_dst[1]
        elif 'ap' in str(src) and str(src) not in self.nodesPlotted:
            ap = src
            pos_0 = pos_src[0]
            pos_1 = pos_src[1]
            
        if 'ap' in str(src) and str(src) not in self.nodesPlotted or 'ap' in str(dst) and str(dst) not in self.nodesPlotted:
            self.plotap[ap], = ax.plot(range(MAX_X), range(MAX_Y), linestyle='', marker='.', ms=12, mfc='red')
            
            ax.add_patch(
                patches.Circle((pos_0, pos_1),
                self.range(ap.mode), fill=True,  alpha=0.1
                )
            )
            self.plotap[ap].set_data(pos_0, pos_1)
            self.nodesPlotted.append(ap)
            plt.text(int(pos_0), int(pos_1), ap)
        
        plt.title("Mininet-WiFi Graph")
        plt.draw()            
        
    @classmethod 
    def getDistance(self, src, dst):
        """ Get the distance between two points """
        pos_src = self.nodePosition[str(src)]
        pos_dst = self.nodePosition[str(dst)]
        if self.plotGraph and self.cancelPlot==False:
            self.plot(src, dst, pos_src, pos_dst)
        points = np.array([(pos_src[0], pos_src[1], pos_src[2]), (pos_dst[0], pos_dst[1], pos_dst[2])])
        dist = distance.pdist(points)
        return dist
    
    @classmethod 
    def printDistance(self, src, dst):
        """ Print the distance between two points """
        self.src = src
        self.dst = dst
        
        dist = self.getDistance(src, dst)
        print ("The distance between %s and %s is %.2f meters\n" % (src, dst, float(dist)))
    
    @classmethod   
    def printPosition(self, node):
        """ Print position of STAs and APs """
        self.node = str(node)
        
        self.pos_x = self.nodePosition[self.node][0]
        self.pos_y = self.nodePosition[self.node][1]
        self.pos_z = self.nodePosition[self.node][2]   
        print "----------------\nPosition of %s\n---------------- \
        \nPosition X: %.2f \
        \nPosition Y: %.2f \
        \nPosition Z: %.2f\n" % (self.node, float(self.pos_x), float(self.pos_y), float(self.pos_z))
        
    @classmethod   
    def handover(self, sta, ap, wlan, distance, changeAP, reason=None, **params):
       
        if distance < self.range(ap.mode): 
            if reason == 'llf' or reason == 'ssf':
                sta.pexec("iw dev %s-wlan%s disconnect" % (sta, wlan))
                sta.pexec("iw dev %s-wlan%s connect %s" % (sta, wlan, ap.ssid))
                sta.ifaceAssociatedToAp[wlan] = str(ap)
            if str(ap) not in sta.ifaceAssociatedToAp:
                if 'ap' not in sta.ifaceAssociatedToAp[wlan]:
                    sta.pexec("iw dev %s-wlan%s connect %s" % (sta, wlan, ap.ssid))
                    sta.ifaceAssociatedToAp[wlan] = str(ap)   
        elif distance > self.range(ap.mode):
            if str(ap) == sta.ifaceAssociatedToAp[wlan]:
                sta.pexec("iw dev %s-wlan%s disconnect" % (sta, wlan))       
                sta.ifaceAssociatedToAp[wlan] = 'wlan'  
            
    @classmethod   
    def models(self, wifiNodes=None, startPosition=None, model=None,
               max_x=None, max_y=None, min_v=None, max_v=None, 
               manual_aprange=-10, n_staMov=None, ismobility=None, llf=False, seed=None,
               **mobilityparam):
        
        accessPoint.manual_apRange = manual_aprange
        self.modelName = model
        self.ismobility = ismobility
        self.leastLoadFirst = llf
        np.random.seed(seed)
        
        # set this to true if you want to plot node positions
        self.DRAW = self.plotGraph
        
        self.cancelPlot = True
        
        # number of nodes
        nr_nodes = n_staMov
        
        # simulation area (units)
        MAX_X, MAX_Y = max_x, max_y
        
        # max and min velocity
        MIN_V, MAX_V = min_v, max_v
        
        # max waiting time
        MAX_WT = 100.
        
        if self.DRAW:
            plt.ion()
            ax = plt.subplot(111)
            line, = ax.plot(range(mobility.MAX_X), range(mobility.MAX_X), linestyle='', marker='.', ms=10, mfc='blue')
            self.plottxt = {}
            
            for node in wifiNodes:
                if 'sta' in str(node) and str(node) not in station.fixedPosition:
                    self.plottxt[str(node)] = ax.annotate(str(node), xy=(0, 0))
                    
                if str(node) in station.fixedPosition:
                    self.plottxt[node] = ax.annotate(node, xy=(self.nodePosition[str(node)][0],self.nodePosition[str(node)][1]))
                    self.plotsta[node], = ax.plot(range(mobility.MAX_X), range(mobility.MAX_Y), linestyle='', marker='.', ms=12, mfc='blue')
                    self.plotsta[node].set_data(self.nodePosition[str(node)][0],self.nodePosition[str(node)][1])
                               
        if(self.modelName=='RandomWalk'):
            ## Random Walk model
            mob = random_walk(nr_nodes, dimensions=(MAX_X, MAX_Y))
        elif(self.modelName=='TruncatedLevyWalk'):
            ## Truncated Levy Walk model
            mob = truncated_levy_walk(nr_nodes, dimensions=(MAX_X, MAX_Y))
        elif(self.modelName=='RandomDirection'):
            ## Random Direction model
            mob = random_direction(nr_nodes, dimensions=(MAX_X, MAX_Y), velocity=(MIN_V, MAX_V))
        elif(self.modelName=='RandomWayPoint'):
            ## Random Waypoint model
            mob = random_waypoint(nr_nodes, dimensions=(MAX_X, MAX_Y), velocity=(MIN_V, MAX_V), wt_max=MAX_WT)
        elif(self.modelName=='GaussMarkov'):
            ## Gauss-Markov model
            mob = gauss_markov(nr_nodes, dimensions=(MAX_X, MAX_Y), alpha=0.99)
        else:
            print 'Model not defined or wrong!'
        
        ## Reference Point Group model
        #groups = [4 for _ in range(10)]
        #nr_nodes = sum(groups)
        #rpg = reference_point_group(groups, dimensions=(MAX_X, MAX_Y), aggregation=0.5)
        
        ## Time-variant Community Mobility Model
        #groups = [4 for _ in range(10)]
        #nr_nodes = sum(groups)
        #tvcm = tvc(groups, dimensions=(MAX_X, MAX_Y), aggregation=[0.5,0.], epoch=[100,100])
        oneTime = []
                
        if model!='':
            try:
                for xy in mob:
                    if self.DRAW:
                        line.set_data(xy[:,0],xy[:,1])
                    for n in range (0,len(wifiNodes)):
                        self.position = []
                        wifiNode = str(wifiNodes[n])
                        ap = wifiNodes[n]
                        sta = wifiNodes[n]
                        if 'ap' in wifiNode and wifiNode not in oneTime:
                            pos_zero = startPosition[wifiNode][0]
                            pos_one = startPosition[wifiNode][1]
                            self.position.append(pos_zero)
                            self.position.append(pos_one)
                            self.position.append(0)
                            self.nodePosition[wifiNode] = self.position                            
                            if self.DRAW:
                                plt.plot([pos_zero], [pos_one], 'ro')
                                plt.text(int(pos_zero), int(pos_one), wifiNode)
                                ax.add_patch(
                                    patches.Circle((pos_zero, pos_one),
                                    self.range(ap.mode), fill=True,  alpha=0.1
                                    )
                                )
                            oneTime.append(str(wifiNodes[n]))
                        elif 'ap' not in str(wifiNodes[n]):
                            if wifiNode not in station.fixedPosition:
                                self.position.append(xy[n][0])
                                self.position.append(xy[n][1])
                                self.position.append(0)
                                if self.DRAW:
                                    self.plottxt[wifiNode].xytext = (xy[n][0], xy[n][1])
                                self.nodePosition[wifiNode] = self.position
                                for ap in accessPoint.name:
                                    distance = self.getDistance(sta, ap)
                                    association.setInfraParameters(wifiNodes[n], ap, distance, '')
                    if self.DRAW:
                        plt.title("Mininet-WiFi Graph")
                        plt.draw()
            except:
                print "Graph Stopped!"  
        
class wifiParameters ( object ):
    """
        WiFi Parameters 
    """
    freq = {}
    txpower = {}
    rsi = {}
    
    
    @classmethod
    def get_rsi(self, sta, iface): 
        """ Get rsi info """
        self.rsi[str(sta)] = (sta.cmd('iwconfig %s | grep -o \'Signal.*\' | cut -f2- -d\'=\' | cut -c1-4'
                                            % iface)) 
    
    @classmethod
    def get_frequency(self, sta, iface): 
        """ Get frequency info **in development """
        freq = sta.cmd('iwconfig %s | grep -o \'Frequency.*z\' | cut -f2- -d\':\' | cut -c1-5'
                                            % iface)
        if freq!='':
            self.freq[str(sta)] = float(freq) 
    
    @classmethod
    def get_tx_power(self, sta, iface): 
        """ Get tx_power info """
        self.txpower[str(sta)] = int(sta.cmd('iwconfig %s | grep -o \'Tx-Power.*\' | cut -f2- -d\'=\' | cut -c1-3'
                                         % iface))
    #@classmethod
    #def printNoiseInfo(self, host): 
    #    """
    #        Get noise info **in development**
    #    """
    #    print self.host.cmd('iw dev %s-wlan0 survey noise %d' % (host, int(str(host)[3:])+60))    
    
    @classmethod
    def latency(self, distance):        
        latency = 2 + distance
        return latency
        
    @classmethod
    def loss(self, distance, mode):  
        if distance!=0:
            loss =  0.1 * distance
        else:
            loss = 0.1
        return loss/10
    
    @classmethod
    def delay(self, distance, seconds):
        """"Based on RandomPropagationDelayModel (ns3)"""
        delay = distance/seconds
        return delay
        
    
    @classmethod
    def custom_step(self, mode):    
        """ only useful for bw """
        self.step = 0
        if (mode=='a' or mode=='g'):
            self.step = 3
        elif(mode=='b'):
            self.step = 5
        elif(mode=='n'):
            self.step = 5
        elif(mode=='ac'):
            self.step = 5
            
        return self.step
    
    @classmethod
    def custom_bw_step(self, mode):    
        """ only useful for bw """
        self.bw_step = 0
        if (mode=='a' or mode=='g'):
            self.bw_step = 5
        elif(mode=='b'):
            self.bw_step = 1.1
        elif(mode=='n'):
            self.bw_step = 42
        elif(mode=='ac'):
            self.bw_step = 338
            
        return self.bw_step
    
    @classmethod
    def bw(self, distance, mode):
       
        signalRange = self.get_range(mode)
        customStep = self.custom_step(mode)
        custombwStep = self.custom_bw_step(mode)
        if distance != 0: 
            bw = self.set_bw(mode)
            for n in range(0,signalRange+1):
                if n % customStep==0:
                    if n>=distance:
                        return bw
                    elif distance > signalRange:
                        return self.set_bw(mode)
                    bw = bw - custombwStep                    
        else:
            return self.set_bw(mode)        

    @classmethod
    def max_pathLoss(self, sta):
        """used to calculate the range."""  
        sta = str(sta)
        gains = 6
        losses = 6
        fademargin = 12
        maxpathloss = self.txpower[sta] - self.rsi[sta] + gains - losses - fademargin
        return maxpathloss
        
    @classmethod
    def friis_propagation_loss_model(self):   
        """
            power_r = Reception Power (W)
            power_t = Transmission Power (W)
            gain_r = Reception gain (unit-less)
            gain_t = Transmission gain (unit-less)
            wavelength = wavelength (m) => C/f => (m/s and Hz)
            distance = (m)
            systemLoss = system loss (unit-less)
        """
        frequency = 2412
        power_t = 20
        gain_r = 6
        gain_t = 6
        systemLoss = 1.
        wavelength = 299792458/frequency
        power_r = (power_t * gain_t * gain_r * math.pow(wavelength,2)) / \
                        math.pow((4 * math.pi * distance),2) * systemLoss
        return power_r
        
    @classmethod
    def pathLoss(self, exponent):
        """(pathloss) is the path loss in decibels
        (exponent) is the path loss exponent
        (distance) is the distance between the transmitter and the receiver (meters)
        and (constant) is a constant which accounts for system losses."""    
        #pathloss = 10 * exponent * math.log10(distance) + constant
    
    @classmethod
    def free_space_loss(self, sta):
        """Formula: Free Space Loss
        (distance) is the distance between the transmitter and the receiver (km)
        (frequency) signal frequency transmited(MegaHertz)."""  
        sta = str(sta)
        frequency = self.freq[sta]
        distance=10
        #32,44 is a constant and its value depends on the units for distance and frequency
        fsl = 32,44 - 20 * math.log10(distance) + 20 * math.log10(frequency) #fsl in dB
        return float('%.1f' % fsl)
    
    @classmethod
    def free_space_path_loss(self, sta):
        """Formula: Free Space Path Loss
        (distance) is the distance between the transmitter and the receiver (meters)
        (frequency) signal frequency transmited(Hertz)
        (constant) speed of light in a vacuum (metres per second)."""  
        sta = str(sta)
        constant = 3 * 10**8  
        frequency = self.freq[sta] * 10**9 # Using 10^9 to convert to Hz 
        distance = 1
        fspl = ((4 * math.pi * distance * frequency)/constant)**2
        return fspl
    
    @classmethod    
    def get_range(self, mode):
        """ get Range (in meters) """
        self.distance = 0
        if (mode=='a' or mode=='g'):
            self.distance = 33
        elif(mode=='b'):
            self.distance = 50
        elif(mode=='n'):
            self.distance = 70
        elif(mode=='ac'):
            self.distance = 100 
        
        self.distance = self.distance
        return self.distance
    
    @classmethod    
    def set_bw(self, mode):
        """ set maximum Bandwidth according Mode """
        self.bandwidth = 0
        if (mode=='a'):
            self.bandwidth = 54
        elif(mode=='b'):
            self.bandwidth = 11
        elif(mode=='g'):
            self.bandwidth = 54 
        elif(mode=='n'):
            self.bandwidth = 600
        elif(mode=='ac'):
            self.bandwidth = 6777 
            
        return self.bandwidth