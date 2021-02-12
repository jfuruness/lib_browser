"""Contains helper funcs for the Browser class"""

from copy import deepcopy
import functools

def switch_to_window():
    """Switches to new window after func if possible"""
    def my_decorator(func):
        @functools.wraps(func)
        def function_that_runs_func(self, *args, **kwargs):
            # Inside the decorator
            og_windows = deepcopy(set(self.browser.window_handles))
            # Run the function
            func(self, *args, **kwargs)
            if len(self.browser.window_handles) != len(og_windows):
                for handle in self.browser.window_handles:
                    if handle not in og_windows:
                        self.browser.switch_to.window(handle)
                        break
                self.switch_to_iframe()
                self.show_links()
        return function_that_runs_func
    return my_decorator
