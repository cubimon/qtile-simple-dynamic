import textwrap
import yaml
from libqtile.layout.base import Layout
from libqtile.window import Window
from libqtile.config import ScreenRect

class Rect:

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __str__(self):
        return 'Rect(x={}, y={}, width={}, height={})'.format(
                self.x, self.y, self.width, self.height)

class WindowWrapper:

    def __init__(self, window=None):
        self.window = window
        if self.window:
            self.wm_class = window.window.get_wm_class()
        else:
            self.wm_class = None

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.window == other.window
        elif isinstance(other, Window):
            return self.window == other
        return False

    def __hash__(self):
        if not self.window:
            return 0
        return self.window.__hash__()

    def __str__(self):
        return 'WindowWrapper({}, wm_class={})'.format(
                str(self.window), self.wm_class)

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
        self.rect = None
        self.redraw = False
        self.root_layout = None

    def clone(self, group):
        c = Layout.clone(self, group)
        c.parent = self.parent
        c.clients = []
        c.client_focus = self.client_focus
        c.rect = None
        c.redraw = self.redraw
        c.root_layout = self.root_layout
        return c

    def add(self, client):
        if client in self.clients:
            return
        if isinstance(client, DynamicBaseLayout):
            client.parent = self
            client.root_layout = self.root_layout
        if isinstance(client, WindowWrapper) and \
                not isinstance(self, self.root_layout.default_layout):
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
        if client in self.clients:
            return
        if isinstance(client, DynamicBaseLayout):
            client.parent = self
            client.root_layout = self.root_layout
        if isinstance(client, WindowWrapper) and \
                not isinstance(self, self.root_layout.default_layout):
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
        if client in self.clients:
            return
        if isinstance(client, DynamicBaseLayout):
            client.parent = self
            client.root_layout = self.root_layout
        if isinstance(client, WindowWrapper) and \
                not isinstance(self, self.root_layout.default_layout):
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
            while layout.client_focus >= len(layout.clients) - 1 and \
                    layout.parent:
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
            horizontal_layout = HorizontalLayout()
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
            horizontal_layout = HorizontalLayout()
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
            vertical_layout = VerticalLayout()
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
            vertical_layout = VerticalLayout()
            self.parent.replace(self, vertical_layout)
            vertical_layout.add(self)
            client_parent = self.root_layout.default_layout()
            vertical_layout.add(client_parent)
            client_parent.add(client)
            return client

    def resize(self, x, y):
        layout = self.focused_layout()
        if not layout:
            return
        vertical_layout = None
        horizontal_layout = None
        while (vertical_layout is None or horizontal_layout is None) and \
                layout.parent:
            if isinstance(layout, VerticalLayout) and not vertical_layout:
                vertical_layout = layout
            if isinstance(layout, HorizontalLayout) and not horizontal_layout:
                horizontal_layout = layout
            layout = layout.parent
        if vertical_layout:
            vertical_layout.resize(0, y)
        if horizontal_layout:
            horizontal_layout.resize(x, 0)

    def reset_size(self):
        for client in self.clients:
            client.rect = None
            if isinstance(client, DynamicBaseLayout):
                client.reset_size()

    def remove(self, client, recursive=True):
        if client in self.clients:
            self.clients.remove(client)
            if len(self.clients) == 0:
                if recursive and self.parent and \
                        self.parent != self.root_layout:
                    return self.parent.remove(self)
            else:
                if self.client_focus > 0:
                    self.client_focus -= 1
                if len(self.clients) > 0:
                    return self.focused_client()
        elif recursive:
            for layout in self.clients:
                if isinstance(layout, DynamicBaseLayout):
                    result = layout.remove(client)
                    if result:
                        return result

    def cleanup(self):
        # removes redundant layouts
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
        if isinstance(self.clients[self.client_focus], WindowWrapper):
            return self
        else:
            return self.clients[self.client_focus].focused_layout()

    def focused_client(self):
        # return focused client
        if len(self.clients) == 0:
            return None
        if isinstance(self.clients[self.client_focus], WindowWrapper):
            return self.clients[self.client_focus]
        else:
            return self.clients[self.client_focus].focused_client()

    def free_client_by_class(self, wm_class):
        # find window wrapper with wm_class without window
        for client in self.clients:
            if isinstance(client, WindowWrapper) and \
                    client.window is None and \
                    client.wm_class == wm_class:
                return client
            elif isinstance(client, DynamicBaseLayout):
                free_client = client.free_client_by_class(wm_class)
                if free_client:
                    return free_client

    def client_layout(self, client):
        # return layout of client, direct parent of client
        if client in self.clients:
            return self
        for layout in self.clients:
            if isinstance(layout, DynamicBaseLayout):
                result = layout.client_layout(client)
                if result:
                    return result

    def all_windows(self):
        # return list of all window wrapper
        result = []
        for client in self.clients:
            if isinstance(client, WindowWrapper):
                result.append(client)
            else:
                result.extend(client.all_windows())
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
            if not isinstance(client, WindowWrapper):
                return False
        return True

    def is_root(self):
        return self.parent == None

    def __str__(self):
        result = '{}(rect={})'.format(type(self).__name__, self.rect)
        clients_result = '\n'.join(map(str, self.clients))
        clients_result = textwrap.indent(clients_result, '  ')
        if len(clients_result) > 0:
            result += '\n' + clients_result
        return result

class VerticalLayout(DynamicBaseLayout):
    '''
    Vertical layout
    '''

    def configure(self, client, screen):
        if not self.rect:
            self.rect = Rect(screen.x, screen.y, screen.width, screen.height)
        if client in self.clients:
            index = self.clients.index(client)
            client_wrapper = self.clients[index]
            if not client_wrapper.rect:
                client_wrapper.rect = Rect(*self.window_size(index))
            client.place(
                client_wrapper.x,
                client_wrapper.y,
                client_wrapper.width,
                client_wrapper.height,
                0,
                None)
            client.unhide()
        else:
            for index, layout in enumerate(self.clients):
                if isinstance(layout, DynamicBaseLayout):
                    if layout.client_layout(client):
                        layout.configure(client,
                                ScreenRect(*self.window_size(index)))

    def window_size(self, index):
        return (
            self.rect.x,
            int(self.rect.y + self.rect.height / len(self.clients) * index),
            self.rect.width,
            int(self.rect.height / len(self.clients)))

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

    def resize(self, x, y):
        focused_layout = self.clients[self.client_focus]
        if focused_layout.rect:
            if 0 < y and y < self.rect.height - focused_layout.rect.height:
                focused_layout.rect.height += y
                ratio = y / (self.rect.height - focused_layout.rect.height)
                inv_ratio = 1.0 - ratio
                for client in self.clients:
                    if client != focused_layout:
                        client.rect.height *= inv_ratio
                        client.rect.height = int(client.rect.height)
            if y < 0 and -y < focused_layout.rect.height:
                focused_layout.rect.height += y
                offset = int(-y / (len(self.clients) - 1))
                for client in self.clients:
                    if client != focused_layout:
                        client.rect.height += offset
            self.fix_resize_issues()

    def fix_resize_issues(self):
        # fix some rounding errors to avoid one pixel gaps
        # also set position values, depending on new size
        y_sum = self.rect.y
        for client in self.clients[:-1]:
            client.rect.y = y_sum
            y_sum += client.rect.height
        self.clients[-1].rect.y = y_sum
        self.clients[-1].rect.height = self.rect.height - (y_sum - self.rect.y)

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

class HorizontalLayout(DynamicBaseLayout):
    '''
    horizontal layout
    '''

    def configure(self, client, screen):
        if not self.rect:
            self.rect = Rect(screen.x, screen.y, screen.width, screen.height)
        if client in self.clients:
            index = self.clients.index(client)
            client_wrapper = self.clients[index]
            if not client_wrapper.rect:
                client_wrapper.rect = Rect(self.window_size(index))
            client.place(
                client_wrapper.x,
                client_wrapper.y,
                client_wrapper.width,
                client_wrapper.height,
                0,
                None)
            client.unhide()
        else:
            for index, layout in enumerate(self.clients):
                if isinstance(layout, DynamicBaseLayout):
                    if layout.client_layout(client):
                        layout.configure(client, 
                                ScreenRect(*self.window_size(index)))

    def window_size(self, index):
        return (
            int(self.rect.x + self.rect.width / len(self.clients) * index),
            self.rect.y,
            int(self.rect.width / len(self.clients)),
            self.rect.height)

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

    def resize(self, x, y):
        focused_layout = self.clients[self.client_focus]
        if focused_layout.rect:
            if 0 < x and x < self.rect.width - focused_layout.rect.width:
                focused_layout.rect.width += x
                ratio = x / (self.rect.width - focused_layout.rect.width)
                inv_ratio = 1.0 - ratio
                for client in self.clients:
                    if client != focused_layout:
                        client.rect.width *= inv_ratio
                        client.rect.width = int(client.rect.width)
            if x < 0 and -x < focused_layout.rect.width:
                focused_layout.rect.width += x
                offset = int(-x / (len(self.clients) - 1))
                for client in self.clients:
                    if client != focused_layout:
                        client.rect.width += offset
            self.fix_resize_issues()

    def fix_resize_issues(self):
        # fix some rounding errors to avoid one pixel gaps
        # also set position values, depending on new size
        x_sum = self.rect.x
        for client in self.clients[:-1]:
            client.rect.x = x_sum
            x_sum += client.rect.width
        self.clients[-1].rect.x = x_sum
        self.clients[-1].rect.width = self.rect.width - (x_sum - self.rect.x)

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

class TabsLayout(DynamicBaseLayout):

    def configure(self, client, screen):
        if not self.rect:
            self.rect = Rect(screen.x, screen.y, screen.width, screen.height)
        if self.clients[self.client_focus] == client:
            client.place(
                self.rect.x,
                self.rect.y,
                self.rect.width,
                self.rect.height,
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

DefaultLayout = TabsLayout

class SimpleDynamic(DynamicBaseLayout):

    defaults = [
        ("default_layout", TabsLayout, "Default layout class")
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
        print('add')
        print(client)
        if isinstance(client, Window):
            # check for empty window wrapper with wm_class
            free_client = self.free_client_by_class(client.window.get_wm_class())
            if free_client:
                free_client.window = client
                print('found reserved space for client')
                print(self)
                return
        self.cleanup()
        if len(self.clients) == 0:
            layout = self.default_layout()
            layout.root_layout = self
            DynamicBaseLayout.add(self, layout)
        if isinstance(client, Window):
            self.focused_layout().add(WindowWrapper(client))
        else:
            self.focused_layout().add(client)
        self.group.layout_all()
        print(self)

    def cmd_focus_left(self):
        client = self.focused_layout().focus_left()
        if client:
            self.group.focus(client.window, True)

    def cmd_focus_right(self):
        client = self.focused_layout().focus_right()
        if client:
            self.group.focus(client.window, True)

    def cmd_focus_up(self):
        client = self.focused_layout().focus_up()
        if client:
            self.group.focus(client.window, True)

    def cmd_focus_down(self):
        client = self.focused_layout().focus_down()
        if client:
            self.group.focus(client.window, True)

    def cmd_shuffle_left(self):
        client = self.focused_layout().shuffle_client_left()
        self.cleanup()
        self.reset_size()
        self.group.layout_all()
        if client:
            self.group.focus(client.window, True)
        print(self)

    def cmd_shuffle_right(self):
        client = self.focused_layout().shuffle_client_right()
        self.cleanup()
        self.reset_size()
        self.group.layout_all()
        if client:
            self.group.focus(client.window, True)
        print(self)

    def cmd_shuffle_up(self):
        client = self.focused_layout().shuffle_client_up()
        self.cleanup()
        self.reset_size()
        self.group.layout_all()
        if client:
            self.group.focus(client.window, True)
        print(self)

    def cmd_shuffle_down(self):
        client = self.focused_layout().shuffle_client_down()
        self.cleanup()
        self.reset_size()
        self.group.layout_all()
        if client:
            self.group.focus(client.window, True)
        print(self)

    def cmd_resize(self, x, y):
        self.focused_layout().resize(x, y)
        self.group.layout_all()
        print(self)

    def cmd_reset_size(self):
        self.reset_size()
        self.group.layout_all()
        print(self)

    def to_tree(self, o):
        if isinstance(o, WindowWrapper):
            return {
                'class_name': o.wm_class[0] + ' - ' + o.wm_class[1]
            }
        else:
            client_list = []
            for client in o.clients:
                client_list.append(self.to_tree(client))
            layout_name = str(o.__class__.__name__)
            if isinstance(o, SimpleDynamic):
                return client_list
            else:
                return {
                    layout_name: client_list,
                    'rect': {
                        'x': o.rect.x,
                        'y': o.rect.y,
                        'width': o.rect.width,
                        'height': o.rect.height
                    }
                }

    def add_from_tree(self, parent, tree):
        if isinstance(tree, list):
            for sub_tree in tree:
                self.add_from_tree(parent, sub_tree)
        elif isinstance(tree, dict):
            if 'class_name' in tree:
                # window wrapper
                window = WindowWrapper(None)
                window.wm_class = tuple(tree['class_name'].split(' - '))
                parent.add(window)
            else:
                # layout
                layout_name = list(tree.keys())[0]
                layout = None
                if layout_name == 'HorizontalLayout':
                    layout = HorizontalLayout()
                elif layout_name == 'VerticalLayout':
                    layout = VerticalLayout()
                elif layout_name == 'TabsLayout':
                    layout = TabsLayout()
                if 'rect' in tree:
                    if 'x' in tree['rect'] and \
                            'y' in tree['rect'] and \
                            'width' in tree['rect'] and \
                            'height' in tree['rect']:
                        rect = Rect(
                                tree['rect']['x'], tree['rect']['y'],
                                tree['rect']['width'], tree['rect']['height'])
                        layout.rect = rect
                if layout:
                    parent.add(layout)
                    self.add_from_tree(layout, tree[layout_name])

    def cmd_save_yaml(self, file_name):
        tree = self.to_tree(self)
        with open(file_name, 'w') as file:
            yaml.dump(tree, file)

    def cmd_load_yaml(self, file_name):
        with open(file_name, 'r') as file:
            tree = yaml.load(file)
            all_windows = self.all_windows()
            self.clients = []
            self.add_from_tree(self, tree)
            for window in all_windows:
                self.add(window.window)
            print('loaded from {}'.format(file_name))
            print(self)

    def remove(self, client):
        if isinstance(client, Window):
            if client.fullscreen:
                return
        client = DynamicBaseLayout.remove(self, client)
        self.cleanup()
        self.reset_size()
        self.group.layout_all()
        if client:
            self.group.focus(client.window, True)
        print('after remove')
        print(self)

