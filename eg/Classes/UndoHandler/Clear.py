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
from eg.Classes.UndoHandler import UndoHandlerBase


class Clear(UndoHandlerBase):
    name = eg.text.MainFrame.Menu.Delete.replace("&", "")

    @eg.AssertInMainThread
    @eg.LogIt
    def Do(self, item):
        if not item.CanDelete() or not item.AskDelete():
            return
        self.data = item.GetFullXml()
        self.treePosition = eg.TreePosition(item)
        eg.actionThread.Func(item.Delete)()
        self.document.AppendUndoHandler(self)


    @eg.AssertInActionThread
    def Undo(self):
        item = self.document.RestoreItem(self.treePosition, self.data)
        item.Select()


    @eg.AssertInActionThread
    def Redo(self):
        self.treePosition.GetItem().Delete()

