# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright (C) 2005-2010 Lars-Peter Voss <bitmonster@eventghost.org>
#
# EventGhost is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the
# Free Software Foundation;
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import wx
import eg
from eg.WinApi.Dynamic import (
        SetClipboardViewer, ChangeClipboardChain, WM_CHANGECBCHAIN,
    WM_DRAWCLIPBOARD, SendMessage
)


class MainMessageReceiver(eg.MessageReceiver):
    
    def __init__(self):
        self.hwndNextViewer = None
        eg.MessageReceiver.__init__(self, "EventGhost Message Receiver")
        
    
    def Setup(self):
        eg.MessageReceiver.Setup(self)
        self.AddHandler(WM_CHANGECBCHAIN, self.OnChangeClipboardChain)
        self.hwndNextViewer = SetClipboardViewer(self.hwnd)
        self.AddHandler(WM_DRAWCLIPBOARD, self.OnDrawClipboard)


    @eg.LogIt
    def OnChangeClipboardChain(self, dummyHwnd, mesg, wParam, lParam):
        # if the next clipboard viewer window is closing, repair the chain.
        if wParam == self.hwndNextViewer:
            self.hwndNextViewer = lParam
            if self.hwndNextViewer == self.hwnd:
                self.hwndNextViewer = None
        elif self.hwndNextViewer:
            SendMessage(self.hwndNextViewer, mesg, wParam, lParam)
        return 0


    def OnDrawClipboard(self, dummyHwnd, mesg, wParam, lParam):
        wx.CallAfter(eg.Notify, "ClipboardChange")
        # pass the message to the next window in the clipboard viewer chain
        if self.hwndNextViewer:
            SendMessage(self.hwndNextViewer, mesg, wParam, lParam)


    def Stop(self):
        ChangeClipboardChain(self.hwnd, self.hwndNextViewer)
        eg.MessageReceiver.Stop(self)
