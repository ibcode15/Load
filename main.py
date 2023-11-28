import time

import os
import sys


class Bar:
    def __init__(
        self,
        name: str,
        update_screen_func,
        on_completion_func,
        on_completion_message: str,
        total: int,
        bar_size: int = 100,
        amount_name="",
        inc: int = 1,
    ):
        self.name = name
        self.update_screen = update_screen_func
        self.on_completion = on_completion_func
        self.on_completion_flag = False
        self.on_completion_message = on_completion_message

        self.displayed_total = total
        self.new_line = " "
        self.bar_size = bar_size
        self.wait_for_others = False
        self.ref_id = None

        self.size_of_displayed_total = len(str(self.displayed_total))
        self.start_size = len(f"{self.name} [")
        self._current = 0
        self.display_current: int = 0

        self.update()

    def progress(self, amount: int):
        amount = int(amount)
        if (self.display_current + amount) > self.displayed_total:
            assert False, "amount given is too much compared to total"
        self.display_current += amount
        self._current += self.inc * amount
        self.update()
        if self.display_current == self.displayed_total:
            self.render = f"{self.name} {self.on_completion_message}"
            self.on_completion_flag = True
            self.on_completion(self.ref_id)
            self.update_screen()

    def resize(self):
        columns, lines = os.get_terminal_size()
        if self.bar_size >= columns:
            self.bar_size = columns - 10

        self.total_size = (
            self.start_size
            + self.bar_size
            + 1
            + self.size_of_displayed_total
            + 1
            + self.size_of_displayed_total
        )
        if len(self.name) >= self.bar_size or self.total_size > columns:
            self.new_line = "\n"
        elif self.total_size < columns:
            self.bar_size += columns - (self.total_size + 4)
            self.total_size += columns - self.total_size
        self.inc = self.bar_size / self.displayed_total
        self.logical_total = self.bar_size
        self._current = self.inc * self.display_current

    def __next__(self):
        if self.display_current < self.displayed_total:
            self._current += self.inc
            self.display_current += 1
            self.update()
            return
        if not self.on_completion_flag:
            self.render = f"{self.name} {self.on_completion_message}"
            self.on_completion_flag = True
            self.on_completion(self.ref_id)
            self.update_screen()
        if self.wait_for_others:
            return

        raise StopIteration

    def __iter__(self):
        return self

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, a):
        self._current = a
        self.update()

    def update(self):
        self.resize()
        self.load = "#" * round(self._current)
        self.space = " " * round(self.logical_total - self._current)
        self.render = f"{self.name}{self.new_line}[{self.load}{self.space}] {self.display_current}/{self.displayed_total}"
        self.update_screen()

    def __repr__(self):
        return self.render


class LoadingBars:
    def __init__(self, max_text: int = 10, on_completion_message: str = None):
        self.bar_ref = 0
        self.__text: list[str] = []
        self.__bars: list = []
        if not on_completion_message:
            self.on_completion_message = "is completed."
        else:
            self.on_completion_message = on_completion_message

        self.enable_VT_console()

        self.__ref_count_list: list[int] = []
        self.max_text = max_text

        self.hide_cursor()
        self.clear_screen_string = "\033[1J\033[500A"  # "\033[1J\033[500A"

    @staticmethod
    def hide_cursor():
        print("\033[?25l")

    @staticmethod
    def show_cursor():
        print("\033[?25h")

    def __on_completion(self, ref_id: int):
        if ref_id == None:
            return
        self.__ref_count_list[ref_id] -= 1

        if self.__ref_count_list[ref_id] == 0:
            self.__ref_count_list[ref_id] = None
            for bar in self.__bars:
                if bar.ref_id == ref_id:
                    bar.wait_for_others = False

    def add_bar(self, name: str, total: int, on_completion_message: str = None) -> Bar:
        if not on_completion_message:
            on_completion_message = self.on_completion_message
        new_bar = Bar(
            name=name,
            update_screen_func=self.update_screen,
            on_completion_func=self.__on_completion,
            on_completion_message=on_completion_message,
            total=total,
        )
        self.__bars.insert(0, new_bar)
        self.update_screen()
        return new_bar

    def next_ref_id(self):
        return len(self.__ref_count_list)

    def enable_VT_console(self):
        if sys.platform == "win32":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            STD_OUTPUT_HANDLE = kernel32.GetStdHandle(-11)
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            ENABLE_PROCESSED_INPUT = 0x0001
            kernel32.SetConsoleMode(
                STD_OUTPUT_HANDLE,
                ENABLE_VIRTUAL_TERMINAL_PROCESSING | ENABLE_PROCESSED_INPUT,
            )

    def update_screen(self):
        print(self.clear_screen_string)
        print("\n".join(self.__text))
        print("\n".join(str(v) for v in self.__bars))

    def display(self, *args, sep=" "):
        self.__text.append(sep.join(args))
        if len(self.__text) > self.max_text:
            self.__text.pop(0)
        self.update_screen()

    def bar_zip(self, *bars):
        bars = set(bars)
        bars_len = len(bars)
        if bars_len <= 1:
            assert False, "bar_zip needs 2 or more bars to work."
        try:
            if ref_id := self.__ref_count_list.index(None):
                self.__ref_count_list[ref_id] = 0
        except:
            ref_id = self.next_ref_id()
            self.__ref_count_list.append(0)
        for bar in set(bars):
            assert (
                bar in self.__bars
            ), "only bars which are part of the same LoadingBars object can be added."
            bar.wait_for_others = True
            bar.ref_id = ref_id
        self.__ref_count_list[ref_id] = bars_len
        return zip(*bars)
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print("\033c")
        self.show_cursor()


if __name__ == "__main__":
    with LoadingBars() as test:
        bar1 = test.add_bar("task 1", 100)
        bar2 = test.add_bar("task 2", 200)
        bar3 = test.add_bar("task 3", 300)
        bar4 = test.add_bar("task 4", 400)
        bar5 = test.add_bar("task 5", 500)
        bar6 = test.add_bar("task 6", 600)
        bar7 = test.add_bar("task 7", 700)
        bar8 = test.add_bar("task 8", 800)
        bar9 = test.add_bar("task 9", 900)
        for i in test.bar_zip(bar1, bar2, bar3, bar4, bar5, bar6, bar7, bar8, bar9):
            time.sleep(0.05)
