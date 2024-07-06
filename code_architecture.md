
I think about this because of the russian doll class imbrication. It's only for more readability and maintainability.

for instance : 

```python
class SettingsMenu:
    def __init__(self):
        self.keybinds_description = KeybindsDescription()

class KeybindsDescription:
    def __init__(self):
        self.keybinds = [Keybinds() for _ in range(10)]

class Keybinds:
    def __init__(self):
        pass
```


# Solution 1

The we have to call `handle_event`, `update` and `draw` for each class.

```python
def event_loop()
    for event in events:
        a.handle_event(event)
        b.handle_event(event)

def update():
    # events
    event_loop()
    # update
    a.update()
    b.update()

    # draw
    a.draw()
    b.draw()
```

# Solution 2

The we have to call `handle_event` and `draw` for each class. `update` is called inside `handle_event`.

```python
def event_loop()
    for event in events:
        a.handle_event(event)
        b.handle_event(event)

def update():
    # update
    event_loop()
    
    # draw
    a.draw()
    b.draw()


class A:
    def handle_event(self, event):
        update()
        event_funcs(event)

    ...

```



# Solution 3

The we have to call `handle` and `update` for each class. 

```python
def event_loop()
    for event in events:
        a.handle_event(event)
        b.handle_event(event)

def update():
    # update
    event_loop()

    a.update()
    b.update()

class A:
    def update():
        update_funcs()
        draw()
```



# Solution 4

I don't like this solution because all classes have to recall `for event in events`, but we dont pass event from classes to classes.

Only `update` is called for each class.


```python
def event_loop()
    for event in events:
        events

def update():
    # events
    event_loop()

    # update
    a.update()
    b.update()

class A:
    def event_loop():
        for event in events:
            events
    
    def update():
        # events
        event_loop()

        # update
        aa.update()
        bb.update()

        # draw
        draw()
        

```


