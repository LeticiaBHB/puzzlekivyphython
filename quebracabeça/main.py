import time
from random import shuffle, randint
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.core.window import Window

class Card(Button):
    def __init__(self, cell_num, board, **kwargs):
        kwargs["on_press"] = self.click_handler
        super(Card, self).__init__(**kwargs)
        self.initial_cellnum = cell_num
        self.cell_num = cell_num
        self.num_cols = board.cols
        self.cell_movex = board.movex
        self.cell_movey = board.movey
        self.move_handler = board.move
        self.cards = board.children
        self.face_value = kwargs["text"]
        self.trigger_rerunner = board.trigger_rerunner
        self.check_rerunner = board.check_rerunner

        # Define as imagens de fundo para cada peça do quebra-cabeça
        # Certifique-se de que as imagens estejam na mesma pasta do arquivo Python
        self.background_normal = f"bird.{cell_num}.jpg"

    def on_size(self, pos_size, *args):
        row_num = self.calc_row_num()
        col_num = self.calc_col_num()
        self.cell_movex[col_num] = self.pos[0]
        self.cell_movey[row_num] = self.pos[1]
        if self == self.cards[0]:
            self.trigger_rerunner()

    def click_handler(self, instance):
        self.move_handler(self, instance)

    def calc_row_num(self):
        return int(self.cell_num / self.num_cols)

    def calc_col_num(self):
        return self.cell_num % self.num_cols

    def on_move_end(self, anim, widget_instance):
        self.check_rerunner()

    def animate_move(self, instance):
        col_num = self.calc_col_num()
        row_num = self.calc_row_num()
        animation = Animation(pos=(self.cell_movex[col_num], self.cell_movey[row_num]), d=0.2)
        animation.bind(on_complete=self.on_move_end)
        animation.start(instance)

    def move_up(self, instance):
        row_num = self.calc_row_num()
        if row_num == 0:
            return
        self.cell_num -= self.num_cols
        self.animate_move(instance)

    def move_right(self, instance):
        col_num = self.calc_col_num()
        if col_num == self.num_cols - 1:
            return
        self.cell_num += 1
        self.animate_move(instance)

    def move_down(self, instance):
        row_num = self.calc_row_num()
        if row_num == self.num_cols - 1:
            return
        self.cell_num += self.num_cols
        self.animate_move(instance)

    def move_left(self, instance):
        col_num = self.calc_col_num()
        if col_num == 0:
            return
        self.cell_num -= 1
        self.animate_move(instance)

class Board(GridLayout):
    def __init__(self, **kwargs):
        super(Board, self).__init__(**kwargs)
        self.cols = kwargs["cols"]
        num_slots = self.cols**2
        board = []
        for i in range(1, num_slots):
            board.append(i)

        while True:
            shuffle(board)
            num_inversions = self.count_inversion(board)
            if num_inversions % 2 == 0:
                break

        self.movex = {}
        self.movey = {}
        self.moves = []
        self.stored_moves = []
        self.rerunner_moves = []
        self.trigger_rerunner = Clock.create_trigger(self.rerunner)
        self.trigger_dorerun = Clock.create_trigger(self.do_rerun)
        self.scheduled_rerun_time = 0
        self.scheduled_rerun = None
        for i in range(0, num_slots-1):
            self.add_widget(Card(i, self, text=str(board[i]), color=[1, 1, 0, 1.0]))
        self.free_cell = num_slots - 1

    def move(self, cell, widget_instance):
        if cell.cell_num - self.cols == self.free_cell:
            self.free_cell = cell.cell_num
            cell.move_up(widget_instance)
            self.moves.append((cell, widget_instance))
        elif cell.calc_col_num() < self.cols - 1 and cell.cell_num + 1 == self.free_cell:
            self.free_cell = cell.cell_num
            cell.move_right(widget_instance)
            self.moves.append((cell, widget_instance))
        elif cell.cell_num + self.cols == self.free_cell:
            self.free_cell = cell.cell_num
            cell.move_down(widget_instance)
            self.moves.append((cell, widget_instance))
        elif cell.calc_col_num() > 0 and cell.cell_num - 1 == self.free_cell:
            self.free_cell = cell.cell_num
            cell.move_left(widget_instance)
            self.moves.append((cell, widget_instance))
        board = [self.cols**2] * (self.cols**2)
        for card in self.children:
            board[card.cell_num] = int(card.face_value)
        inversion = self.count_inversion(board)
        if inversion == 0:
            print("solved")

    def count_inversion(self, board):
        inversions_all = 0
        for i, val in enumerate(board[0:-1]):
            for after in board[i+1:len(board)]:
                if after < val:
                    inversions_all += 1
        return inversions_all

    def on_size(self, *args):
        self.free_cell = self.cols**2 - 1
        for card in self.children:
            card.cell_num = card.initial_cellnum

    def randomly_destroy_images(self, percentage=30):
        num_cards = len(self.children)
        num_cards_to_destroy = int(num_cards * percentage / 100)
        cards_to_destroy = [randint(0, num_cards - 1) for _ in range(num_cards_to_destroy)]

        for i in range(num_cards):
            card = self.children[i]
            if i in cards_to_destroy:
                # Replace the card's background with an empty image to "destroy" it
                card.background_normal = ""
            else:
                # Restore the card's original background image
                card.background_normal = f"bird.{card.initial_cellnum}.jpg"

    def rerunner(self, *args):
        if self.moves and not self.rerunner_moves:
            if self.scheduled_rerun_time > 0:
                self.scheduled_rerun.cancel()
            self.scheduled_rerun_time = time.time()
            self.scheduled_rerun = Clock.schedule_once(self.do_rerun, 0.5)

    def do_rerun(self, *args):
        self.scheduled_rerun_time = 0
        if self.rerunner_moves:
            move = self.rerunner_moves.pop(0)
            self.move(move[0], move[1])
            return
        if self.moves and not self.rerunner_moves:
            self.rerunner_moves = self.moves.copy()
            self.stored_moves = self.moves.copy()
            self.moves.clear()
            move = self.rerunner_moves.pop(0)
            self.move(move[0], move[1])

    def check_rerunner(self):
        if self.rerunner_moves:
            self.trigger_dorerun()

class Ui(BoxLayout):
    def __init__(self, **kwargs):
        super(Ui, self).__init__(**kwargs)
        self.board = None

    def create_board(self, num_cols):
        if self.board is not None:
            self.board.clear_widgets()
            self.remove_widget(self.board)
        self.board = Board(cols=num_cols, size_hint=(1, 1), spacing=0, padding=0)
        self.board.randomly_destroy_images()  # Call the method to randomly destroy images
        self.add_widget(self.board)

class SlidePuzzle(App):
    def build(self):
        myui = Ui()
        myui.create_board(7)  # Defina o número de colunas do quebra-cabeça aqui (neste exemplo, 7)
        return myui

if __name__ == '__main__':
    Window.clearcolor = (0, 0, 0, 0)  # Define a cor de fundo para branco
    SlidePuzzle().run()

