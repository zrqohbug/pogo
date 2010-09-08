import sys, os

import gtk

if __name__ == '__main__':
    base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../'))
    sys.path.insert(0, base_dir)

from extTreeview import ExtTreeView

from tools import consts

# The format of a row in the treeview
(
    ROW_ICO, # Item icon
    ROW_NAME,     # Item name
    ROW_TRK,   # The track object
) = range(3)

# Internal d'n'd (reordering)
DND_REORDERING_ID   = 1024
DND_INTERNAL_TARGET = ('extListview-internal', gtk.TARGET_SAME_WIDGET, DND_REORDERING_ID)

class TrackTreeView(ExtTreeView):
    def __init__(self, colums, use_markup=True):
        ExtTreeView.__init__(self, colums, use_markup)
        
        # Drag'n'drop management
        self.dndContext    = None
        self.dndSources    = None
        self.dndTargets    = consts.DND_TARGETS.values()
        self.motionEvtId   = None
        self.dndStartPos   = None
        self.dndReordering = False

        self.dndStartPos     = None
        self.isDraggableFunc = lambda: True
        
        if len(self.dndTargets) != 0:
            # Move one name around while dragging
            # self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, \
            #        self.dndTargets+[DND_INTERNAL_TARGET], gtk.gdk.ACTION_MOVE)
            self.enable_model_drag_dest(self.dndTargets, gtk.gdk.ACTION_DEFAULT)
        
        self.connect('drag-begin', self.onDragBegin)
        self.connect('drag-motion', self.onDragMotion)
        self.connect('drag-data-received', self.onDragDataReceived)
        
        self.connect('button-press-event', self.onButtonPressed)
        
        self.mark = None
        
    def insert(self, target, source_row, drop_mode=None):
        model = self.store
        if drop_mode == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
            new = model.prepend(target, source_row)
        elif drop_mode == gtk.TREE_VIEW_DROP_INTO_OR_AFTER or drop_mode is None:
            new = model.append(target, source_row)
        elif drop_mode == gtk.TREE_VIEW_DROP_BEFORE:
            new = model.insert_before(None, target, source_row)
        elif drop_mode == gtk.TREE_VIEW_DROP_AFTER:
            new = model.insert_after(None, target, source_row)
        return new
        
    def appendRow(self, row, parent_iter=None):
        """ Append a row to the tree """
        return self.store.append(parent_iter, row)
        
    def removeRow(self, iter):
        """ Remove the given row """
        self.store.remove(iter)
        
    def getSelectedRows(self):
        sel_paths = self.selection.get_selected_rows()[1]
        return [self.store.get_iter(path) for path in sel_paths]
        
    def getFirstSelectedRow(self):
        sel_rows = self.getSelectedRows()
        if sel_rows:
            return sel_rows[0]
        return None
        
    def iterSelectedRows(self):
        """ Iterate on selected rows """
        for iter in self.getSelectedRows():
            yield iter
            
    def removeSelectedRows(self):
        '''
        Remove the rows in reverse order.
        Otherwise we remove the wrong rows, 
        because the paths will have changed
        '''
        for iter in reversed(self.getSelectedRows()):
            self.removeRow(iter)
        
    def setItem(self, iter, colIndex, value):
        """ Change the value of the given item """
        self.store.set_value(iter, colIndex, value)
        
    def getItem(self, iter, colIndex):
        """ Return the value of the given item """
        return self.store.get_value(iter, colIndex)
        
    def getTrack(self, iter):
        return self.getItem(iter, ROW_TRK)
        
    def scroll(self, iter):
        self.scroll_to_cell(self.store.get_path(iter))
        
    def expand(self, iter):
        self.expand_to_path(self.store.get_path(iter))
        
    def get_nodename(self, iter):
        if not iter:
            return 'None'
        return self.store.get_value(iter, 1)
        
    def get_first_iter(self):
        return self.store.get_iter_root()
        
    def get_last_iter(self):
        return self.get_lowest_descendant(self.get_lowest_root())
        
    def get_lowest_root(self):
        root_nodes = len(self.store)
        if root_nodes == 0:
            return None
        return self.store.iter_nth_child(None, root_nodes-1)        
        
    def iter_prev(self, iter):
        path = self.store.get_path(iter)
        position = path[-1]
        if position == 0:
            return None
        prev_path = list(path)[:-1]
        prev_path.append(position - 1)
        prev = self.store.get_iter(tuple(prev_path))
        return prev
        
    def get_prev_iter(self, iter=None):
        '''
        Look for the previous iter in the tree
        '''
        #assert self.mark
        if iter is None:
            iter = self.getMark()
            
        # Check for a sibling or its children
        prev_iter = self.iter_prev(iter)
        if prev_iter:
            return self.get_lowest_descendant(prev_iter)
            
        # Check for the parent
        parent_iter = self.store.iter_parent(iter)
        if parent_iter:
            return parent_iter
        return None
        
    def get_next_iter(self, iter=None):
        '''
        Look for the next iter in the tree
        '''
        #assert self.mark
        if iter is None:
            iter = self.getMark()
            
        # Check for a child
        if self.store.iter_has_child(iter):
            first_child = self.store.iter_nth_child(iter, 0)
            return first_child
            
        # Check for a sibling
        next_iter = self.store.iter_next(iter)
        if next_iter:
            return next_iter
            
        # iter has no following siblings -> return uncle
        return self.get_uncle(iter)
            
    def get_uncle(self, iter):
        while True:
            parent = self.store.iter_parent(iter)
            if parent is None:
                # We have reached the top of the tree
                return None
            uncle = self.store.iter_next(parent)
            if uncle:
                return uncle
            iter = parent
            
    def get_lowest_descendant(self, iter):
        '''
        Find lowest descendant or return iter
        - a    -> c
          - b  -> b
          - c  -> c
        - d    -> d
        '''
        descendant = None
        if self.store.iter_has_child(iter):
            last_child = self.get_last_child_iter(iter)
            descendant = self.get_lowest_descendant(last_child)
        return descendant or iter
        
    def get_last_child_iter(self, iter):
        ''''''
        if not self.store.iter_has_child(iter):
            return None
        children = self.store.iter_n_children(iter)
        return self.store.iter_nth_child(iter, children-1)
        
    def get_last_iter_on_same_level(self, iter):
        ''''''
        parent = self.store.iter_parent(iter)
        if parent:
            return self.get_last_child_iter(parent)
        while True:
            sibling = self.store.iter_next(iter)
            if not sibling:
                return iter
            iter = sibling
    
        
    # --== Mark management ==--


    def hasMark(self):
        """ True if a mark has been set """
        return self.mark is not None


    def clearMark(self):
        """ Remove the mark """
        if self.mark is not None:
            ##self.setItem(self.mark, self.markColumn, False)
            self.mark = None


    def getMark(self):
        """ Return the iter of the marked row """
        if not self.mark:
            return self.setMark(self.store.get_iter_root())
        return self.store.get_iter(self.mark.get_path())


    def setMark(self, iter):
        """ Put the mark on the given row, it will move with the row itself (e.g., D'n'D) """
        self.clearMark()
        self.mark = gtk.TreeRowReference(self.store, self.store.get_path(iter))
        
    
    # DRAG AND DROP
    
    def move_selected_rows(self, x, y):
        '''
        Method called when dnd happens inside the treeview
        '''
        drop = self.get_dest_row_at_pos(int(x), int(y))
        selection = self.getSelectedRows()
        
        model = self.store
        
        if drop:
            dest, drop_mode = drop
            dest = model.get_iter(dest)
        else:
            # Dropped on free space -> append
            dest, drop_mode = self.get_last_iter(), gtk.TREE_VIEW_DROP_AFTER
            
        self.freeze_child_notify()
        
        # filter selected tracks whose directories have been selected too
        iters = []
        for iter in selection:
            add = True
            for checked_iter in iters:
                if model.is_ancestor(checked_iter, iter):
                    add = False
            if add:
                iters.append(iter)
        
        # Move the iters
        for index, iter in enumerate(iters):
            #TODO: Handle Mark
            if index > 0:
                drop_mode = gtk.TREE_VIEW_DROP_AFTER
            
            track = self.getTrack(iter)
            if track:
                row = model[iter]
                dest = self.insert(dest, row, drop_mode)
            else:
                dest = self.move_dir(iter, dest, drop_mode)
            
        for iter in iters:
            model.remove(iter)
        
        self.thaw_child_notify()
        
        
    def move_dir(self, dir_iter, target, drop_mode):
        '''
        Recursive Method that moves a dir to target
        '''
        children = self.store[dir_iter].iterchildren()
        dir_row = self.store[dir_iter]
        new_target = self.insert(target, dir_row, drop_mode)
        for child in children:
            child = child.iter
            track = self.getTrack(child)
            row = self.store[child]
            if track:
                self.insert(new_target, row, gtk.TREE_VIEW_DROP_INTO_OR_AFTER)
            else:
                self.move_dir(child, new_target, gtk.TREE_VIEW_DROP_INTO_OR_AFTER)
        return new_target
            
        
    def enableDNDReordering(self):
        """ Enable the use of Drag'n'Drop to reorder the list """
        self.dndReordering = True
        self.dndTargets.append(DND_INTERNAL_TARGET)
        self.enable_model_drag_dest(self.dndTargets, gtk.gdk.ACTION_DEFAULT)
        
    
    def onDragBegin(self, tree, context):
        """ A drag'n'drop operation has begun """
        if self.getSelectedRowsCount() == 1: context.set_icon_stock(gtk.STOCK_DND,          0, 0)
        else:                                context.set_icon_stock(gtk.STOCK_DND_MULTIPLE, 0, 0)


    def onDragDataReceived(self, tree, context, x, y, selection, dndId, time):
        """ Some data has been dropped into the list """
        if dndId == DND_REORDERING_ID:
            self.move_selected_rows(x, y)
        else:
            self.emit('extlistview-dnd', context, int(x), int(y), selection, dndId, time)


    def onDragMotion(self, tree, context, x, y, time):
        """
        Allow the following drops:
        - tracks onto and into dir
        - tracks between dirs
        - dir between dirs
        
        -> Prevent the drops:
        - dir into dir
        - anything into track
        """
        drop = self.get_dest_row_at_pos(int(x), int(y))

        if drop is not None:
            iter = self.store.get_iter(drop[0])
            self.setItem(self.get_first_iter(), 1, str(drop[1])[1:-1])
            track = self.getTrack(iter)
            if track and (drop[1] == gtk.TREE_VIEW_DROP_INTO_OR_AFTER or drop[1] == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                # do not let the user drop anything here
                self.enable_model_drag_dest([('invalid-position', 0, -1)], gtk.gdk.ACTION_DEFAULT)
                return
        # Everything ok, enable dnd
        self.enable_model_drag_dest(self.dndTargets, gtk.gdk.ACTION_DEFAULT)
        
        
if __name__ == '__main__':    
    from gobject import TYPE_STRING, TYPE_INT, TYPE_PYOBJECT
    
    from tools import icons
    from media import getTracks
    
    tracks = getTracks(['/home/jendrik/Musik/Clearlake - Amber'])
    #print tracks
    
    columns = (('',   [(gtk.CellRendererPixbuf(), gtk.gdk.Pixbuf), (gtk.CellRendererText(), TYPE_STRING)], True),
                   (None, [(None, TYPE_INT)],                                                                 False),
                   (None, [(None, TYPE_STRING)],                                                               False),
                   (None, [(None, TYPE_PYOBJECT)], False),
                  )
                  
    tree = TrackTreeView(columns, True)
    
    track = None
    
    
    
    a = tree.appendRow((icons.nullMenuIcon(), 'a', 1, 'something', track), None)
    b = tree.appendRow((icons.nullMenuIcon(), 'b', 1, 'something', track), a)
    c = tree.appendRow((icons.nullMenuIcon(), 'c', 1, 'something', track), a)
    d = tree.appendRow((icons.nullMenuIcon(), 'd', 1, 'something', track), None)
    
    for iter in [a, b, c, d]:
        next = tree.get_next_iter(iter)
        print tree.get_nodename(iter), '->', tree.get_nodename(next)
        
    for iter in [a, b, c, d]:
        uncle = tree.get_uncle(iter)
        print 'Uncle(%s) = %s' % (tree.get_nodename(iter), tree.get_nodename(uncle))
        
    for iter in [a, b, c, d]:
        prev = tree.get_prev_iter(iter)
        print tree.get_nodename(prev), '<-', tree.get_nodename(iter)
        
    for iter in [a, b, c, d]:
        res = tree.get_last_iter_on_same_level(iter)
        print 'Last Sibling(%s) = %s' % (tree.get_nodename(iter), tree.get_nodename(res))
        
    for iter in [a, b, c, d]:
        res = tree.get_lowest_descendant(iter)
        print 'Lowest Descendant(%s) = %s' % (tree.get_nodename(iter), tree.get_nodename(res))
        
    res = tree.get_last_iter()
    print 'Last node: %s' % tree.get_nodename(res)
    
    win = gtk.Window()
    win.set_size_request(400,300)
    win.connect('destroy', lambda x: sys.exit())
    win.add(tree)
    tree.expand_all()
    
    win.show_all()
    gtk.main()