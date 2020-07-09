import textwrap
from libqtile.layout.base import Layout
from libqtile.window import Window
from libqtile.config import ScreenRect

'''
Windows are leaves
up/left is previous
down/right is next
'''
class DynamicBaseLayout(Layout):

    def __init__(self, **config):
        Layout.__init__(self, **config)
        self.parent = None
        self.clients = []
        self.client_focus = 0
        self.redraw = False
        self.root_layout = None

    def clone(self, group):
        c = Layout.clone(self, group)
        c.parent = self.parent
        c.clients = []
        c.client_focus = self.client_focus
        c.redraw = self.redraw
        c.root_layout = self.root_layout
        return c

    def add(self, client):
        if isinstance(client, DynamicBaseLayout):
            client.parent = self
            client.root_layout = self.root_layout
        if isinstance(client, Window) \
                and not isinstance(self, self.root_layout.default_layout):
            direct_parent = self.root_layout.default_layout()
            direct_parent.parent = self
            direct_parent.root_layout = self.root_layout
            self.clients.insert(self.client_focus + 1, direct_parent)
            direct_parent.clients = [client]
        else:
            self.clients.insert(self.client_focus + 1, client)
        self.focus(client)
        return client 

    def add_beginning(self, client):
        if isinstance(client, DynamicBaseLayout):
            client.parent = self
            client.root_layout = self.root_layout
        if isinstance(client, Window) \
                and not isinstance(self, self.root_layout.default_layout):
            direct_parent = self.root_layout.default_layout()
            direct_parent.parent = self
            direct_parent.root_layout = self.root_layout
            self.clients.insert(0, direct_parent)
            direct_parent.clients = [client]
        else:
            self.clients.insert(0, client)
        self.focus(client)
        return client

    def add_end(self, client):
        if isinstance(client, DynamicBaseLayout):
            client.parent = self
            client.root_layout = self.root_layout
        if isinstance(client, Window) \
                and not isinstance(self, self.root_layout.default_layout):
            direct_parent = self.root_layout.default_layout()
            direct_parent.parent = self
            direct_parent.root_layout = self.root_layout
            self.clients.append(direct_parent)
            direct_parent.clients = [client]
        else:
            self.clients.append(client)
        self.focus(client)
        return client

    def replace(self, client, new_client):
        if client in self.clients:
            if isinstance(client, DynamicBaseLayout):
                new_client.parent = self
                new_client.root_layout = self.root_layout
            self.clients[self.clients.index(client)] = new_client

    def cmd_next(self):
        client = self.focus_next()
        self.group.focus(client, True)

    def cmd_previous(self):
        client = self.focus_previous()
        self.group.focus(client, True)

    def focus(self, client):
        layout = self.client_layout(client)
        layout.client_focus = layout.clients.index(client)
        client = layout
        layout = layout.parent
        while layout:
            layout.client_focus = layout.clients.index(client)
            client = layout
            layout = layout.parent

    def focus_first(self):
        focused_layout = self.focused_layout()
        if focused_layout != self:
            return focused_layout.focus_first()
        else:
            self.client_focus = 0
            if len(self.clients) > 0:
                return self.clients[self.client_focus]

    def focus_last(self):
        focused_layout = self.focused_layout()
        if focused_layout != self:
            return focused_layout.focus_last()
        else:
            if len(self.clients) > 0:
                self.client_focus = len(self.clients) - 1
                return self.clients[self.client_focus]

    def focus_next(self):
        layout = self.focused_layout()
        if layout != self:
            return layout.focus_next()
        else:
            while layout.client_focus >= len(layout.clients) - 1 \
                    and layout.parent:
                layout = layout.parent
            if layout.client_focus < len(layout.clients) - 1:
                layout.client_focus += 1
                return layout.clients[layout.client_focus]

    def focus_previous(self):
        layout = self.focused_layout()
        if layout != self:
            return layout.focus_previous()
        else:
            while layout.client_focus <= 0 and layout.parent:
                layout = layout.parent
            if layout.client_focus > 0:
                layout.client_focus -= 1
                return layout.clients[layout.client_focus]

    def focus_left(self):
        if self.parent and not self.parent.is_root():
            return self.parent.focus_left()

    def focus_right(self):
        if self.parent and not self.parent.is_root():
            return self.parent.focus_right()

    def focus_up(self):
        if self.parent and not self.parent.is_root():
            return self.parent.focus_up()

    def focus_down(self):
        if self.parent and not self.parent.is_root():
            return self.parent.focus_down()

    def shuffle_client_left(self, client=None):
        layout = self.left_layout()
        if layout:
            client = self.clients[self.client_focus]
            self.remove(client, recursive=False)
            return layout.add_end(client)
        else:
            client = self.clients[self.client_focus]
            self.remove(client, recursive=False)
            horizontal_layout = Horizontal()
            self.parent.replace(self, horizontal_layout)
            client_parent = self.root_layout.default_layout()
            horizontal_layout.add(client_parent)
            client_parent.add(client)
            horizontal_layout.add(self)
            return client

    def shuffle_client_right(self, client=None):
        layout = self.right_layout()
        if layout:
            client = self.clients[self.client_focus]
            self.remove(client, recursive=False)
            return layout.add_beginning(client)
        else:
            client = self.clients[self.client_focus]
            self.remove(client, recursive=False)
            horizontal_layout = Horizontal()
            self.parent.replace(self, horizontal_layout)
            horizontal_layout.add(self)
            client_parent = self.root_layout.default_layout()
            horizontal_layout.add(client_parent)
            client_parent.add(client)
            return client

    def shuffle_client_up(self, client=None):
        layout = self.up_layout()
        if layout:
            client = self.clients[self.client_focus]
            self.remove(client, recursive=False)
            layout.add_end(client)
        else:
            client = self.clients[self.client_focus]
            self.remove(client, recursive=False)
            vertical_layout = Vertical()
            self.parent.replace(self, vertical_layout)
            client_parent = self.root_layout.default_layout()
            vertical_layout.add(client_parent)
            client_parent.add(client)
            vertical_layout.add(self)
            return client

    def shuffle_client_down(self, client=None):
        layout = self.down_layout()
        if layout:
            client = self.clients[self.client_focus]
            self.remove(client, recursive=False)
            return layout.add_beginning(client)
        else:
            client = self.clients[self.client_focus]
            self.remove(client, recursive=False)
            vertical_layout = Vertical()
            self.parent.replace(self, vertical_layout)
            vertical_layout.add(self)
            client_parent = self.root_layout.default_layout()
            vertical_layout.add(client_parent)
            client_parent.add(client)
            return client

    def remove(self, client, recursive=True):
        if client in self.clients:
            self.clients.remove(client)
            if len(self.clients) == 0:
                if recursive and self.parent \
                        and self.parent != self.root_layout:
                    return self.parent.remove(self)
            else:
                if self.client_focus == len(self.clients):
                    self.client_focus = len(self.clients) - 1
                if len(self.clients) > 0:
                    return self.focused_client()
        elif recursive:
            for layout in self.clients:
                if isinstance(layout, DynamicBaseLayout):
                    result = layout.remove(client)
                    if result:
                        return result

    def cleanup(self):
        for leaf in self.leaf_layouts():
            node = leaf
            while node and node != node.root_layout:
                if len(node.clients) == 0:
                    node = node.parent.remove(node)
                    break
                else:
                    node = node.parent
        for leaf in self.leaf_layouts():
            node = leaf
            while node != node.root_layout:
                if not isinstance(node, self.root_layout.default_layout):
                    if len(node.clients) == 1:
                        node.parent.replace(node, node.clients[0])
                node = node.parent

    def left_layout(self):
        if self.parent:
            return self.parent.left_layout()

    def right_layout(self):
        if self.parent:
            return self.parent.right_layout()

    def up_layout(self):
        if self.parent:
            return self.parent.up_layout()

    def down_layout(self):
        if self.parent:
            return self.parent.down_layout()

    def focused_layout(self):
        # return focused layout, direct parent
        if len(self.clients) == 0:
            return self
        if isinstance(self.clients[self.client_focus], Window):
            return self
        else:
            return self.clients[self.client_focus].focused_layout()

    def focused_client(self):
        # return focused client
        if len(self.clients) == 0:
            return None
        if isinstance(self.clients[self.client_focus], Window):
            return self.clients[self.client_focus]
        else:
            return self.clients[self.client_focus].focused_client()

    def client_layout(self, client):
        # return layout of client, direct parent of client
        if client in self.clients:
            return self
        for layout in self.clients:
            if isinstance(layout, DynamicBaseLayout):
                result = layout.client_layout(client)
                if result:
                    return result

    def leaf_layouts(self):
        # return all leaves of this, layout
        result = []
        for layout in self.clients:
            if isinstance(layout, DynamicBaseLayout):
                if layout.is_leaf_layout():
                    result.append(layout)
                else:
                    result.extend(layout.leaf_layouts())
        return result

    def is_leaf_layout(self):
        # true if all clients are windows
        for client in self.clients:
            if not isinstance(client, Window):
                return False
        return True

    def is_root(self):
        return self.parent == None

    def __str__(self):
        result = type(self).__name__
        clients_result = '\n'.join(map(str, self.clients))
        clients_result = textwrap.indent(clients_result, '  ')
        if len(clients_result) > 0:
            result += '\n' + clients_result
        return result

class Vertical(DynamicBaseLayout):
    '''
    Vertical layout
    '''

    def configure(self, client, screen):
        if client in self.clients:
            index = self.clients.index(client)
            window_size = self.window_size(screen, index)
            client.place(
                window_size.x,
                window_size.y,
                window_size.width,
                window_size.height,
                0,
                None)
            client.unhide()
        else:
            for index, layout in enumerate(self.clients):
                if isinstance(layout, DynamicBaseLayout):
                    if layout.client_layout(client):
                        inner_screen_size = self.window_size(screen, index)
                        layout.configure(client, inner_screen_size)

    def window_size(self, screen, index):
        return ScreenRect(
            screen.x,
            int(screen.y + screen.height / len(self.clients) * index),
            screen.width,
            int(screen.height / len(self.clients)))

    def focus_up(self):
        if self.client_focus > 0:
            self.client_focus -= 1
            return self.focused_client()
        else:
            return DynamicBaseLayout.focus_up(self)

    def focus_down(self):
        if self.client_focus < len(self.clients) - 1:
            self.client_focus += 1
            return self.focused_client()
        else:
            return DynamicBaseLayout.focus_down(self)

    def shuffle_client_up(self, client=None):
        if self.client_focus > 0 and not client:
            focused_element = self.clients[self.client_focus]
            self.clients.remove(focused_element)
            self.client_focus -= 1
            self.clients.insert(self.client_focus, focused_element)
            return self.focused_client()
        else:
            return DynamicBaseLayout.shuffle_client_up(self, client)

    def shuffle_client_down(self, client=None):
        if self.client_focus < len(self.clients) - 1:
            focused_element = self.clients[self.client_focus]
            self.clients.remove(focused_element)
            self.client_focus += 1
            self.clients.insert(self.client_focus, focused_element)
            return self.focused_client()
        else:
            return DynamicBaseLayout.shuffle_client_down(self, client)

    def up_layout(self):
        if self.client_focus > 0:
            up_client = self.clients[self.client_focus - 1]
            if isinstance(up_client, DynamicBaseLayout):
                return up_client
        else:
            return DynamicBaseLayout.up_layout(self)

    def down_layout(self):
        if self.client_focus < len(self.clients) - 1:
            down_client = self.clients[self.client_focus + 1]
            if isinstance(down_client, DynamicBaseLayout):
                return down_client
        else:
            return DynamicBaseLayout.down_layout(self)

class Horizontal(DynamicBaseLayout):
    '''
    horizontal layout
    '''

    def configure(self, client, screen):
        if client in self.clients:
            index = self.clients.index(client)
            window_size = self.window_size(screen, index)
            client.place(
                window_size.x,
                window_size.y,
                window_size.width,
                window_size.height,
                0,
                None)
            client.unhide()
        else:
            for index, layout in enumerate(self.clients):
                if isinstance(layout, DynamicBaseLayout):
                    inner_screen_size = self.window_size(screen, index)
                    if layout.client_layout(client):
                        layout.configure(client, inner_screen_size)

    def window_size(self, screen, index):
        return ScreenRect(
            int(screen.x + screen.width / len(self.clients) * index),
            screen.y,
            int(screen.width / len(self.clients)),
            screen.height)

    def focus_left(self):
        if self.client_focus > 0:
            self.client_focus -= 1
            return self.focused_client()
        else:
            return DynamicBaseLayout.focus_left(self)

    def focus_right(self):
        if self.client_focus < len(self.clients) - 1:
            self.client_focus += 1
            return self.focused_client()
        else:
            return DynamicBaseLayout.focus_right(self)

    def shuffle_client_left(self, client=None):
        if self.client_focus > 0:
            focused_element = self.clients[self.client_focus]
            self.clients.remove(focused_element)
            self.client_focus -= 1
            self.clients.insert(self.client_focus, focused_element)
            return self.focused_client()
        else:
            return DynamicBaseLayout.shuffle_client_left(self, client)

    def shuffle_client_right(self, client=None):
        if self.client_focus < len(self.clients) - 1:
            focused_element = self.clients[self.client_focus]
            self.clients.remove(focused_element)
            self.client_focus += 1
            self.clients.insert(self.client_focus, focused_element)
            return self.focused_client()
        else:
            return DynamicBaseLayout.shuffle_client_right(self, client)

    def left_layout(self):
        if self.client_focus > 0:
            left_client = self.clients[self.client_focus - 1]
            if isinstance(left_client, DynamicBaseLayout):
                return left_client
        else:
            return DynamicBaseLayout.left_layout(self)

    def right_layout(self):
        if self.client_focus < len(self.clients) - 1:
            right_client = self.clients[self.client_focus + 1]
            if isinstance(right_client, DynamicBaseLayout):
                return right_client
        else:
            return DynamicBaseLayout.right_layout(self)

class Tabs(DynamicBaseLayout):

    def configure(self, client, screen):
        if self.clients[self.client_focus] == client:
            client.place(
                screen.x,
                screen.y,
                screen.width,
                screen.height,
                0,
                None)
            client.unhide()
            return
        else:
            layout = self.clients[self.client_focus]
            if isinstance(layout, DynamicBaseLayout):
                if layout.client_layout(client):
                    layout.configure(client, screen)
                    return
        client.hide()

    def focus_left(self):
        if self.client_focus > 0:
            self.client_focus -= 1
            return self.focused_client()
        else:
            return DynamicBaseLayout.focus_left(self)

    def focus_right(self):
        if self.client_focus < len(self.clients) - 1:
            self.client_focus += 1
            return self.focused_client()
        else:
            return DynamicBaseLayout.focus_right(self)

    def shuffle_client_left(self, client=None):
        if self.client_focus > 0:
            focused_element = self.clients[self.client_focus]
            self.clients.remove(focused_element)
            self.client_focus -= 1
            self.clients.insert(self.client_focus, focused_element)
            return self.focused_client()
        else:
            return DynamicBaseLayout.shuffle_client_left(self, client)

    def shuffle_client_right(self, client=None):
        if self.client_focus < len(self.clients) - 1:
            focused_element = self.clients[self.client_focus]
            self.clients.remove(focused_element)
            self.client_focus += 1
            self.clients.insert(self.client_focus, focused_element)
            return self.focused_client()
        else:
            return DynamicBaseLayout.shuffle_client_right(self, client)

DefaultLayout = Tabs

class SimpleDynamic(DynamicBaseLayout):

    defaults = [
        ("default_layout", Tabs, "Default layout class")
    ]

    def __init__(self, **config):
        DynamicBaseLayout.__init__(self, **config)
        self.root_layout = self
        self.add_defaults(SimpleDynamic.defaults)

    def clone(self, group):
        c = DynamicBaseLayout.clone(self, group)
        c.root_layout = c
        c.default_layout = self.default_layout
        return c

    def configure(self, client, screen):
        for layout in self.clients:
            if isinstance(layout, DynamicBaseLayout):
                if layout.client_layout(client):
                    layout.configure(client, screen)

    def add(self, client):
        if len(self.clients) == 0:
            layout = self.default_layout()
            layout.root_layout = self
            DynamicBaseLayout.add(self, layout)
        self.focused_layout().add(client)
        self.cleanup()
        print(self)

    def focus_left(self):
        client = self.focused_layout().focus_left()
        self.group.focus(client, True)

    def focus_right(self):
        client = self.focused_layout().focus_right()
        self.group.focus(client, True)

    def focus_up(self):
        client = self.focused_layout().focus_up()
        self.group.focus(client, True)

    def focus_down(self):
        client = self.focused_layout().focus_down()
        self.group.focus(client, True)

    def shuffle_left(self):
        client = self.focused_layout().shuffle_client_left()
        self.cleanup()
        print(self)
        self.group.layout_all()
        self.group.focus(client, True)

    def shuffle_right(self):
        client = self.focused_layout().shuffle_client_right()
        self.cleanup()
        print(self)
        self.group.layout_all()
        self.group.focus(client, True)

    def shuffle_up(self):
        client = self.focused_layout().shuffle_client_up()
        self.cleanup()
        print(self)
        self.group.layout_all()
        self.group.focus(client, True)

    def shuffle_down(self):
        client = self.focused_layout().shuffle_client_down()
        self.cleanup()
        print(self)
        self.group.layout_all()
        self.group.focus(client, True)

    def remove(self, client):
        client = DynamicBaseLayout.remove(self, client)
        self.cleanup()
        print(self)
        self.group.layout_all()
        self.group.focus(client, True)

