#
# plugins/MceRemote_Vista/__init__.py
#
# Copyright (C) 2005 Lars-Peter Voss
#
# This file is part of EventGhost.
# 
# EventGhost is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# EventGhost is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with EventGhost; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#


eg.RegisterPlugin(
    name = "Microsoft MCE Remote - Vista/Win7",
    author = "Brett Stottlemyer",
    version = "1.0.2",
    kind = "remote",
    guid = "{A7DB04BB-9F0A-486A-BCA1-CA87B9620D54}",
    description = 'Plugin for the Microsoft MCE remote.  Requires installation of AlternateMceIrService.',
    url = "http://www.eventghost.net/forum/viewtopic.php?f=2&t=1789",
    icon = (
        "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAACfklEQVR42q2TS2gTQRyH"
        "f5N9NNlts20abYyxVirWShGLUh8XoSpUUBEVUU+5CXoQr+LNm14UtRCpRcGLHnqoiooN"
        "VO1FRWrTaKgmqdJqGuwj3TTZ947bbLV37cAMM8zMx39+fEPwn42sGKD7zk3aeWg3TEut"
        "rC3bdrpZmZuWBlVXYFgGKKEQOAHDg+M4f/YCqQBuxa7T7XtaEWloRkkrwDQt6KZzwdZR"
        "VGSU1DmoRgm6pUBWC1DUMoK1q2BmQ24F77/G6ZfvI2isb0FRnYVYZtAe8aCUkzGSyuCj"
        "tADFLsEwNOi0CM1QYDnVrNcOuICHQzfoWCaJoD8MWZnGfoPB1k0BpN/k8DKbxvAGE1JA"
        "QHidF9lMHvnChPMuii3sCRdwre8czUykwDAMuLKKU1oV2CCL7Itx9LMycmtqsa2jAY1N"
        "EgaepWBxc2A5Dq30mAu40neGpr59AKUUliHB5z8KUwxi5vUDWCQNW2TRvrOpknkykYRQ"
        "7wXr4bFRO+ICrj6J0tHcq0ris3MHwbdcgiaX8XMohl2B+xAF4jyhBsqCgqQTsOhnwXNe"
        "NM4fdgG3By7S4amnoBaHT4m9gP84ivkUquf7cTL8Fh1tPjSv9eHxqIw48YL3MfBWiQj/"
        "6nIBzxN3afxHDJYTzLvBOvBMGfMFPyLcZ3QFCtixWcCiET1pFVpIAiE2aqrrEM4vAZIT"
        "Q/RR6jKo1zmgOrLYtAIzphSEZ2cQ8gGTio0E5SGFa6BrBiJSKxqm97mAWE83VUJjSEzG"
        "nXT5v34ugkqKDkPW4OEZCCIH4iEg1IPOttPQ0quXVe6910vh6EuX/F5U1hmWZV/a+LP0"
        "EBbRaJSs3Gf61/YbN1kg0OJlna4AAAAASUVORK5CYII="
    ),
)


import eg
import time
from threading import Timer, Thread
import win32file
import win32pipe
import win32api
import win32event
import _winreg as reg
from struct import unpack_from, unpack, pack
from pronto import Pronto2MceTimings, ConvertIrCodeToProntoRaw
prontoClock = 0.241246
#The Mce Driver parameters are 32 bits long on 32 bit OS's and 64 on 64 bit OS's
#ptr_fmt is a global that is set once per installation, so we can use the correct size
ptr_fmt = None
ptr_len = 4

class TransmitIR(eg.ActionBase):
    name = "Transmit IR"
    
    def __call__(self, code="", repeatCount=0):
        if self.plugin.client is None:
            return
        #Send pronto code:
        freq, transmitValues = Pronto2MceTimings(code,repeatCount)
        transmitCode = RoundAndPackTimings(transmitValues)                        
        n = len(transmitCode)
        #Port is set to zero, it is populated automatically
        header = pack(7*ptr_fmt,2,int(1000000./freq),0,0,0,1,len(transmitCode))
        transmitData = header + transmitCode
        self.plugin.client.Transmit(transmitData)
        
    def Configure(self, code='', repeatCount=0):
        text = self.text
        panel = eg.ConfigPanel()        
        editCtrl = panel.TextCtrl(code, style=wx.TE_MULTILINE)
        font = editCtrl.GetFont()
        font.SetFaceName("Courier New")
        editCtrl.SetFont(font)
        editCtrl.SetMinSize((-1, 100))
        
        repeatCtrl = eg.SpinIntCtrl(panel, -1, value=repeatCount, min=0, max=127)
        repeatCtrl.SetInitialSize((50, -1))
        
        learnButton = panel.Button("Learn an IR Code...")  
        result = self.plugin.client.GetDeviceInfo()
        if result is None or result[2] != 2:
            learnButton.Enable(False)    
            
        panel.sizer.Add(panel.StaticText("Pronto Code"),0,wx.EXPAND)
        panel.sizer.Add((5, 5))
        panel.sizer.Add(editCtrl,0,wx.EXPAND)
        panel.sizer.Add((5, 5))
        panel.sizer.Add(eg.HBoxSizer(panel.StaticText("Repeat Counter:"),(5,5),repeatCtrl,
                        ((5,5),1,wx.EXPAND),(learnButton,0,wx.ALIGN_RIGHT)),0,wx.EXPAND)

        def LearnIR(event):
            code = self.plugin.client.LearnIR()
            if not code is None:
                editCtrl.SetValue(code)
        learnButton.Bind(wx.EVT_BUTTON, LearnIR)
        
        while panel.Affirmed():
            panel.SetResult(
                editCtrl.GetValue(),
                repeatCtrl.GetValue()
            )

class IRLearnDialog(wx.Dialog):
    
    def __init__(self):
        self.code = None
        wx.Dialog.__init__(
            self, 
            None, 
            -1,
            "Learn IR Code",
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
        )
        helpText = "1. Aim remote directly at IR Receiver\n"\
                "approximately 3 inches from Receiver face.\n\n"\
                "2. PRESS the desired button on your remote.\n\n"\
                "3. The dialog will close automatically when\n"\
                "a code is received."                
        staticText = wx.StaticText(self, -1, helpText)
        
        sb = wx.StaticBox(self, -1, "Frequency")
        carrierFreqSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        self.carrierFreqCtrl = wx.StaticText(self, -1, "-", style=wx.ALIGN_CENTER)
        carrierFreqSizer.Add(self.carrierFreqCtrl, 1, wx.EXPAND|wx.ALL, 5)
        
        cancelButton = wx.Button(self, wx.ID_CANCEL, eg.text.General.cancel)
        cancelButton.Bind(wx.EVT_BUTTON, self.OnCancel)

        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(staticText, 0, wx.EXPAND|wx.TOP, 5)
        
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer.Add(cancelButton, 0, wx.EXPAND|wx.ALIGN_RIGHT)
        rightSizer.Add((0, 0), 1)
        rightSizer.Add(carrierFreqSizer, 0, wx.EXPAND)
        rightSizer.Add((0, 0), 1)        
        
        upperRowSizer = wx.BoxSizer(wx.HORIZONTAL)
        upperRowSizer.Add(leftSizer, 1, wx.EXPAND)
        upperRowSizer.Add((5, 5))
        upperRowSizer.Add(rightSizer, 0, wx.EXPAND)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(upperRowSizer, 1, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        self.SetMinSize(self.GetSize())
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.exit = 0

    def OnClose(self, event):
        event.Skip()
        
    def OnCancel(self, event):
        self.Close()

    def GotCode(self, freqs, code):
        median_freq = sorted(freqs)[len(freqs)/2]
        #the following line causes EG to crash
        #self.carrierFreqCtrl.SetLabel(
        #    "%d.%03d kHz" % (median_freq / 1000, median_freq % 1000)
        #)
        self.code = ConvertIrCodeToProntoRaw(median_freq,code)
        self.exit = 1
        self.Close()
        
class GetDeviceInfo(eg.ActionBase):
    name = "Get Mce IR device capability"
    
    def __call__(self):
        if self.plugin.client is None:
            return
        result = self.plugin.client.GetDeviceInfo()
        if result is None:
            eg.PrintNotice("IR Service not running")
            return
        if result[1] == 0 and result[2] == 0:
            eg.PrintNotice("IR Receiver is unplugged")
            return
        nAttached = 0
        i = 0
        while (result[5] >> i) > 0:
            if result[5] & (1 << i):
                nAttached = nAttached + 1
            i = i + 1
        eg.PrintNotice("%d Transmitters (%d attached), %s have learn capability" % 
                        (result[1],nAttached,"does" if result[2] == 2 else "does not"))
        #eg.PrintNotice("Blaster Data: %d"%result)

class TestIR(eg.ActionBase):
    name = "Test IR Transmit capability"
    
    def __call__(self):
        if self.plugin.client is None:
            return
        result = self.plugin.client.GetDeviceInfo()
        if result is None:
            eg.PrintNotice("IR Service not running")
            return
        if result[1] == 0 and result[2] == 0:
            eg.PrintNotice("IR Receiver is unplugged")
            return
        nAttached = 0
        i = 0
        while (result[5] >> i) > 0:
            if result[5] & (1 << i):
                nAttached = nAttached + 1
            i = i + 1
        eg.PrintNotice("%d Transmitters (%d attached), %s have learn capability" % 
                        (result[1],nAttached,"does" if result[2] == 2 else "does not"))
        result = self.plugin.client.TestIR()
        #eg.PrintNotice("result = %d"%result)
        
class SetLearnMode(eg.ActionBase):
    name = "Switch IR Receiver to learn port"
    
    def __call__(self):
        if self.plugin.client is None:
            return
        mode = "l".encode("ascii")
        self.plugin.client.ChangeReceiveMode(mode)
        
class SetNormalMode(eg.ActionBase):
    name = "Switch IR Receiver to normal port"
    
    def __call__(self):
        if self.plugin.client is None:
            return
        mode = "n".encode("ascii")
        self.plugin.client.ChangeReceiveMode(mode)
        
def CheckForMceDriver():
    """
    Checks the HID registry values.
    """
    HID_SUB_KEY = "SYSTEM\\CurrentControlSet\\Services\\HidIr\\Remotes\\745a17a0-74d3-11d0-b6fe-00a0c90f57d"
    noKeyCount = 0
    ValuesToCheck = ['a','b']
    for a in ValuesToCheck:
        tmpkey = HID_SUB_KEY+a
        try:
            key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, tmpkey, 0, reg.KEY_READ)
        except WindowsError:
            noKeyCount = noKeyCount + 1
            continue
    if noKeyCount == len(ValuesToCheck):
        return False
    return True
    
def CheckForAlternateService():
    """
    Checks if the AlternateMceIrService is installed
    """
    ServiceKey = "SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\AlternateMceIrService"
    try:
        key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, ServiceKey, 0, reg.KEY_READ)
    except:
        return False
    return True
            
def RoundAndPackTimings(timingData):
    out = ""
    for v in timingData:
        newVal = 50*int(round(v/50))
        out = out + pack("i",newVal)
    return out
    
class MceMessageReceiver(object):
    """
    Connect to AlternateMceIrService in a new threading.Thread.  This class is callable, so can be assigned to a thread.
    """
    
    def __init__(self,plugin):
        """
        This initializes the class, and saves the plugin reference for use in the new thread.
        """
        self.plugin = plugin
        self.file = None

    @eg.LogIt
    def __call__(self):
        """
        This makes the class callable, and is the entry point for starting the processing in a new thread.
        """
        self.keepRunning = True
        self.learnDialog = None
        self.learnTimeout = 250 #250 msec
        #eg.PrintNotice("MCE_Vista: thread started")
        while self.keepRunning:
            self.Connect()
            if self.keepRunning:
                self.HandleData()
                
    @eg.LogIt
    def Stop(self):
        """
        This will be called to stop the thread.
        """
        if self.file:
            writeOvlap = win32file.OVERLAPPED()
            writeOvlap.hEvent = win32event.CreateEvent(None, 0, 0, None)   
            msg = "q".encode("ascii")
            win32file.WriteFile(self.file, msg, writeOvlap)
            win32file.CloseHandle(self.file)
            self.file = None
        self.keepRunning = False
        #eg.PrintNotice("MCE_Vista: stopping thread")
        
    def Transmit(self, transmitData):
        """
        This will be called to detect available IR Blasters.
        """
        if not self.file:
            return False
        writeOvlap = win32file.OVERLAPPED()
        writeOvlap.hEvent = win32event.CreateEvent(None, 0, 0, None)   
        win32file.WriteFile(self.file, transmitData, writeOvlap)
        win32event.WaitForSingleObject(writeOvlap.hEvent, win32event.INFINITE)
        return True
    
    def LearnIR(self):
        if not self.learnDialog is None: #already have dialog open
            return None
        if not self.ChangeReceiveMode("l".encode("ascii")):
            return None
        code = None
        #reset some variables for learning
        self.freqs = [0]
        self.result = []
        self.learnDialog = IRLearnDialog()
        self.learnDialog.ShowModal()
        if self.learnDialog.exit == 1:
            code = self.learnDialog.code
        #self.learnDialog.Destroy()
        self.ChangeReceiveMode("n".encode("ascii"))
        #reset some variables for normal processing
        self.learnDialog = None
        self.freqs = [0]
        self.result = []
        return code
        
    def GetDeviceInfo(self):
        """
        This will be called to detect IR device info.
        """
        if not self.file:
            return None
        writeOvlap = win32file.OVERLAPPED()
        writeOvlap.hEvent = win32event.CreateEvent(None, 0, 0, None)   
        self.deviceInfoEvent = win32event.CreateEvent(None, 0, 0, None)
        win32file.WriteFile(self.file, "b".encode("ascii"), writeOvlap)
        if win32event.WaitForSingleObject(self.deviceInfoEvent, 250) == win32event.WAIT_OBJECT_0:
            return self.deviceInfo
        return None

    def TestIR(self):
        """
        This will be called to Transmit a known signal to verify blaster capability.
        """
        if not self.file:
            return None
        writeOvlap = win32file.OVERLAPPED()
        writeOvlap.hEvent = win32event.CreateEvent(None, 0, 0, None)   
        self.deviceTestEvent = win32event.CreateEvent(None, 0, 0, None)
        win32file.WriteFile(self.file, "t".encode("ascii"), writeOvlap)
        if win32event.WaitForSingleObject(self.deviceTestEvent, 250) == win32event.WAIT_OBJECT_0:
            return None
        return None
        
    def ChangeReceiveMode(self, mode):
        """
        This will be called to detect available IR Blasters.
        """
        if not(mode == "l" or mode == "n"):
            return False#needs to be normal or learn
        if not self.file:
            return False
        writeOvlap = win32file.OVERLAPPED()
        writeOvlap.hEvent = win32event.CreateEvent(None, 0, 0, None)   
        win32file.WriteFile(self.file, mode, writeOvlap)
        win32event.WaitForSingleObject(writeOvlap.hEvent, win32event.INFINITE)
        return True
        
    def Connect(self):
        """
        This function tries to connect to the named pipe from AlternateMceIrService.  If it can't connect, it will periodically
        retry until the plugin is stopped or the connection is made.
        """
        #eg.PrintNotice("MCE_Vista: Connect started")
        self.sentMessageOnce = False
        while self.file is None and self.keepRunning:
            try:
                self.file = win32file.CreateFile(r'\\.\pipe\MceIr',win32file.GENERIC_READ
                                        |win32file.GENERIC_WRITE,0,None,
                                        win32file.OPEN_EXISTING,win32file.FILE_ATTRIBUTE_NORMAL
                                        |win32file.FILE_FLAG_OVERLAPPED,None)
            except:
                if not self.sentMessageOnce:
                    eg.PrintNotice("MCE_Vista: MceIr pipe is not available, app doesn't seem to be running")
                    eg.PrintNotice("    Will continue to try to connect to MceIr")
                    eg.PrintNotice("    Message = %s"%win32api.FormatMessage(win32api.GetLastError()))
                    self.sentMessageOnce = True
                time.sleep(.25)
        return

    def HandleData(self):
        """
        This runs once a connection to the named pipe is made.  It receives the ir data and passes it to the plugins IRDecoder.
        """
        if self.sentMessageOnce:
            eg.PrintNotice("MCE_Vista: Connected to MceIr pipe, started handling IR events")
        nMax = 2048;
        self.result = []
        self.freqs = [0]
        self.readOvlap = win32file.OVERLAPPED()
        self.readOvlap.hEvent = win32event.CreateEvent(None, 0, 0, None)
        handles = [self.plugin.hFinishedEvent,self.readOvlap.hEvent]
        self.timeout = win32event.INFINITE
        while self.keepRunning:
            try:
                (hr,data) = win32file.ReadFile(self.file,nMax,self.readOvlap)
            except:
                win32file.CloseHandle(self.file)
                self.file = None
                return
            rc = win32event.WaitForMultipleObjects(handles, False, self.timeout)
            if rc == win32event.WAIT_OBJECT_0: #Finished event
                self.keepRunning = False
                break
            elif rc == win32event.WAIT_TIMEOUT: #Learn timeout
                #eg.PrintNotice("LearnTimeout: Sending ir code %s"%str(self.result))
                self.learnDialog.GotCode(self.freqs,self.result)
                self.result = []
                self.timeout = win32event.INFINITE
                rc = win32event.WaitForMultipleObjects(handles, False, self.timeout)
                if rc == win32event.WAIT_OBJECT_0: #Finished event
                    self.keepRunning = False
                    break
            try:
                nGot = self.readOvlap.InternalHigh
                if nGot == 0:
                    continue
                if nGot % ptr_len == 1: #Query result, not ir code data
                    if data[0] == "b".encode("ascii"):
                        self.deviceInfo = unpack_from(6*ptr_fmt,data[1:nGot])
                        win32event.SetEvent(self.deviceInfoEvent)
                    elif data[0] == "t".encode("ascii"):
                        win32event.SetEvent(self.deviceTestEvent)
                    continue
                #pull of the header data
                while nGot > 0:
                    header = unpack_from(3*ptr_fmt,data)
                    if header[0] == 1 and header[2] > 0:
                        self.freqs.append(header[2])
                    dataEnd = nGot
                    if nGot > 100 + 3*ptr_len:
                        dataEnd = 100 + 3*ptr_len
                    nGot -= dataEnd
                    val_data = data[3*ptr_len:dataEnd]
                    dataEnd = dataEnd - 3*ptr_len
                    vals = unpack_from((dataEnd/4)*"i",val_data)
                    data = data[100 + 3*ptr_len:]
                    for i,v in enumerate(vals):
                        a = abs(v)
                        self.result.append(a)                   
                        if self.learnDialog is None: #normal mode
                            if a > 6500: #button held?
                                if self.CodeValid(self.result):
                                    #eg.PrintNotice("Sending ir code %s"%str(self.result))
                                    self.plugin.irDecoder.Decode(self.result, len(self.result))
                                self.result = []
                    if not self.learnDialog is None: #learn mode
                        if header[0] == 1: #one "learn" chunk
                            self.timeout = self.learnTimeout
            except:
                pass
        #eg.PrintNotice("MCE_Vista: Handle Data finished")
    
    def CodeValid(self,code):
        """
        Used to sanity check a code so we don't waste cycles testing it in all the decoders.
        Put any validation of codes (before sending them to IrDecode) in here.
        """
        if len(code) < 5:
            return False
        return True
                
class MCE_Vista(eg.IrDecoderPlugin):
    """
    MCE plugin designed to work with Vista/Win7 and UAC.  It starts a new thread to connect with the AlternateMceIrService
    and receive IR events for AlternateMceIrService's namedpipe.
    """
    
    def __init__(self):
        eg.IrDecoderPlugin.__init__(self,1.0)
        self.AddAction(GetDeviceInfo)
        self.AddAction(TransmitIR)
        self.AddAction(TestIR)
        self.AddAction(SetLearnMode, hidden = True)
        self.AddAction(SetNormalMode, hidden = True)
        self.client = None
        
    def __close__(self):
        self.irDecoder.Close()          
        
    @eg.LogIt
    def __start__(self):
        global ptr_fmt
        global ptr_len
        self.info.eventPrefix = "MceRemote"
        if ptr_fmt == None: #Need to set this once per installation, depending on 32 or 64 bit OS
            from os import environ
            ptr_fmt = "i" #pack/unpack format for 32 bit int
            if environ.get("PROCESSOR_ARCHITECTURE") == "AMD64" or environ.get("PROCESSOR_ARCHITEW6432") == "AMD64":
                ptr_fmt = "q" #pack/unpack format for 64 bit int
                ptr_len = 8
        self.hFinishedEvent = win32event.CreateEvent(None, 1, 0, None)
        try:
            self.remoteList = self.irDecoder.SetKeyMappingFromFile(self.__class__.__name__)
        except:
            pass
        self.client = MceMessageReceiver(self)
        self.msgThread = Thread(target=self.client)
        self.msgThread.start()
              
    def __stop__(self):
        eg.PrintNotice("MCE_Vista: Stopping Mce Vista plugin")
        win32event.SetEvent(self.hFinishedEvent)
        self.client.Stop()
        self.client = None

    def Configure(self, dummy=True):
        from eg.WinApi.PipedProcess import ExecAsAdministrator
        from os.path import join, dirname
        import sys
        #print "CheckForMceDriver",str(CheckForMceDriver())
        #print "CheckForAlternateService",str(CheckForAlternateService())
        scriptPath = join(dirname(__file__.decode(sys.getfilesystemencoding())), "Install.py")
        panel = eg.ConfigPanel()
        installButton = panel.Button("Install Service")
        def OnInstallButton(event):
            ExecAsAdministrator(scriptPath, "Install")
        installButton.Bind(wx.EVT_BUTTON, OnInstallButton)
        uninstallButton = panel.Button("Uninstall Service")
        def OnUnInstallButton(event):
            ExecAsAdministrator(scriptPath, "Uninstall")
        uninstallButton.Bind(wx.EVT_BUTTON, OnUnInstallButton)
        panel.sizer.Add(installButton)
        panel.sizer.Add((10, 10))
        panel.sizer.Add(uninstallButton)
        while panel.Affirmed():
            panel.SetResult()        