# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright (C) 2005-2009 Lars-Peter Voss <bitmonster@eventghost.org>
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

import eg
import wx
import sys
import traceback
import weakref
from types import ModuleType


class Config(eg.PersistentData):
    size = (600, 420)
    position = (10, 10)



class PythonScript(eg.ActionBase):
    name = "Python Script"
    description = "Full featured Python script."
    iconFile = "icons/PythonScript"

    def GetLabel(self, dummySourceCode=""):
        return self.name


    def Configure(self, sourceCode=""):
        panel = eg.ConfigPanel(resizable=True)
        editCtrl = eg.PythonEditorCtrl(panel, value=sourceCode)
        panel.sizer.Add(editCtrl, 1, wx.EXPAND)
        panel.dialog.FinishSetup()
        panel.dialog.SetPosition(Config.position)
        panel.dialog.SetSize(Config.size)
        eg.Utils.EnsureVisible(panel.dialog)
        while panel.Affirmed():
            panel.SetResult(editCtrl.GetValue())
        if not panel.dialog.IsMaximized():
            Config.size = panel.dialog.GetSizeTuple()
            Config.position = panel.dialog.GetPositionTuple()


    class Compile:
        idCounter = 0
        scriptDict = weakref.WeakValueDictionary()

        def __init__(self, sourceCode=""):
            idCounter = self.__class__.idCounter
            self.mod = ModuleType(str(idCounter))
            self.sourceCode = sourceCode
            self.__class__.idCounter += 1
            try:
                self.code = compile(
                    sourceCode + "\n", str(idCounter), "exec", 0, 1
                )
            except:
                self.code = None
                eg.PrintError("Error compiling script.")
                self.PrintTraceback()
            self.scriptDict[idCounter] = self


        def __call__(self):
            if self.code is None:
                self.__init__(self.sourceCode)
                if self.code is None:
                    return
            mod = self.mod
            oldResult = eg.result
            mod.result = oldResult
            try:
                exec(self.code, mod.__dict__) # pylint: disable-msg=W0122
            except SystemExit:
                pass
            except:
                self.PrintTraceback()
            if eg.result is not oldResult:
                return eg.result
            else:
                return mod.result


        def PrintTraceback(self):
            treeItem = eg.currentItem
            treeItem.PrintError("Traceback (most recent call last):")
            lines = self.sourceCode.splitlines()
            tbType, tbValue, tbTraceback = sys.exc_info()
            for entry in traceback.extract_tb(tbTraceback)[1:]:
                filename, linenum, funcname, source = entry
                filename = filename.decode('mbcs')
                try:
                    filenum = int(filename)
                except:
                    filenum = None
                if source is None and filenum is not None:
                    treeItem.PrintError(
                        '  Python script "%s", line %d, in %s' % (
                            filename, linenum, funcname
                        )
                    )
                    lines = self.scriptDict[filenum].sourceCode.splitlines()
                    treeItem.PrintError('    ' + lines[linenum-1].lstrip())
                else:
                    treeItem.PrintError(
                        '  File "%s", line %d, in %s' % (
                            filename, linenum, funcname
                        )
                    )
                    if source is not None:
                        treeItem.PrintError('    ' + source.lstrip())
            name = tbType if type(tbType) == type("") else tbType.__name__
            treeItem.PrintError(str(name) + ': ' + str(tbValue))


        @eg.LogIt
        def __del__(self):
            pass

