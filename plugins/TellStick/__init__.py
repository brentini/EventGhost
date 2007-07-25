#
# plugins/TellStick/__init__.py
#
# Copyright (C) 2007 Telldus Technologies
#

import eg

eg.RegisterPlugin(
    name = "TellStick",
    author = "Micke Prag",
    version = "0.1.1",
    kind = "external",
    description = (
        '<p>Plugin to control TellStick devices.</p>'
        '\n\n<p><a href="http://www.telldus.se">Telldus Hompage</a></p>'
        '<center><img src="tellstick.png" /></center>'
    ),
)

import wx

from ctypes import windll, c_char_p

class TellStick(eg.PluginClass):

    def __init__(self):
        self.AddAction(TurnOn)
        self.AddAction(TurnOff)

    def __start__(self):
        try:
            self.dll = windll.LoadLibrary("TellUsbD101.dll")
        except: 
            raise eg.Exception("TellUsbD101.dll not found.")



class DeviceBase(object):

    def GetLabel(self, device):
        return self.name + " " + (c_char_p(self.plugin.dll.devGetName(device))).value

    def Configure(self, device=0):
        dialog = eg.ConfigurationDialog(self)
        deviceList = []
        numDevices = self.plugin.dll.devGetNumberOfDevices()
        selected = 0
        for i in range(numDevices):
            id = self.plugin.dll.devGetDeviceId(i)
            name = (c_char_p(self.plugin.dll.devGetName(id))).value
            if (id == device):
                selected = i
            deviceList.append(name)
        deviceCtrl = wx.Choice(dialog, -1, choices=deviceList)
        deviceCtrl.Select(selected)
        dialog.sizer.Add(
            wx.StaticText(dialog, -1, "Device:"), 
            0, 
            wx.ALIGN_CENTER_VERTICAL
        )
        dialog.sizer.Add(deviceCtrl, 0, wx.ALIGN_CENTER_VERTICAL)
        if dialog.AffirmedShowModal():
            return (self.plugin.dll.devGetDeviceId(deviceCtrl.GetSelection()), )

class TurnOn(DeviceBase, eg.ActionClass):
    name = "Turn on"
    description = "Turns on a TellStick device."
    iconFile = "lamp-on"

    def __call__(self, device):
        ret = self.plugin.dll.devTurnOn(device)
        if (ret <> True):
            raise eg.Exception("An error occurred while trying to transmit")


class TurnOff(DeviceBase, eg.ActionClass):
    name = "Turn off"
    description = "Turns off a TellStick device."
    iconFile = "lamp-off"

    def __call__(self, device):
        ret = self.plugin.dll.devTurnOff(device)
        if (ret <> True):
            raise eg.Exception("An error occurred while trying to transmit")