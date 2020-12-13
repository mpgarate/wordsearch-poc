import base64
import random
import string
import struct
import sys
import zlib

from enum import Enum

BOARD_SIZE = 5
NUM_SEED_BITS = 63

letters = list(string.ascii_lowercase)

board = []

class Dir(object):
    """
    A Move direction in the path a word makes in the board grid
    """
    N = 0
    NE = 1
    E = 2
    SE = 3
    S = 4
    SW = 5
    W = 6
    NW = 7

class BitPacker(object):
    """
    Build a url safe, compressed, bit-packed representation of data
    """
    def __init__(self):
        self.data = 0
        self.pos_bits = 0

    def add(self, n: int, size_bits: int):
        self.data += (n << self.pos_bits)
        self.pos_bits += size_bits

    def as_base64(self) -> str:
        # length rounded up to the nearest 8 bits
        length = (self.data.bit_length() + 7) // 8
        data_bytes = self.data.to_bytes(length, byteorder='big')

        return base64.urlsafe_b64encode(zlib.compress(data_bytes))


class BitReader(object):
    """
    Decode a url safe, compressed, bit-packed representation of data
    """
    def __init__(self, data_b64: str):
        self.data = int.from_bytes(
            zlib.decompress(base64.urlsafe_b64decode(data_b64)),
            byteorder='big')

    def read(self, size_bits: int) -> int:
        result = self.data & ((1 << size_bits) - 1)
        self.data = self.data >> size_bits

        return result

class Word(object):
    """
    Represent a guessed word on the game board
    """
    def __init__(self, start_row, start_col, moves=[]):
        self.start_row = start_row
        self.start_col = start_col
        self.moves = moves

    def __repr__(self):
        return f"{self.start_row}, {self.start_col}, {self.moves}"


class Board(object):
    """
    A game board where you search for words with connecting letters in a grid
    """
    def __init__(self, seed=None, words=[]):
        self.seed = seed if seed is not None else random.getrandbits(NUM_SEED_BITS)
        self.board = self._gen_board()
        self.words = words

    def _gen_board(self):
        rand = random.Random(self.seed)
        board = []

        for _ in range(0, BOARD_SIZE):
            # TODO: consider a weighted distribution of letters, i.e. ensure some vowels
            board.append([rand.choice(letters) for _ in range(0, BOARD_SIZE)])

        return board

    def add_word(self, start_row, start_col, moves=[]):
        # TODO: validate the word is valid
        self.words.append(Word(start_row, start_col, moves))

    def __str__(self):
        return (f"seed: {self.seed}"
            + "\nencoded: " + BoardSerializer.to_base64(board)
            + "\n\n" + "\n".join(" ".join(row) for row in self.board)
            + "\n\n" + "\n".join(str(w) for w in self.words)
        )

class BoardSerializer(object):
    @staticmethod
    def to_base64(board: Board) -> str:
        bits = BitPacker()

        bits.add(board.seed, NUM_SEED_BITS)

        # assume not more than 256 words found
        bits.add(len(board.words), 8)

        for word in board.words:
            bits.add(word.start_row, 3)
            bits.add(word.start_col, 3)

            # assume no words longer than 15 chars
            bits.add(len(word.moves), 4)

            for move in word.moves:
                bits.add(move, 3)

        return bits.as_base64().decode('utf-8')

    @staticmethod
    def from_base64(data: str):
        bits = BitReader(data)

        seed = bits.read(NUM_SEED_BITS)

        num_words = bits.read(8)

        words = []

        for _ in range(0, num_words):
            start_row = bits.read(3)
            start_col = bits.read(3)

            num_moves = bits.read(4)

            moves = [bits.read(3) for _ in range(0, num_moves)]

            words.append(Word(start_row, start_col, moves))

        return Board(seed, words)


board = Board()
board.add_word(0, 1, [Dir.S, Dir.S, Dir.E, Dir.NE])
board.add_word(1, 3, [Dir.E, Dir.S, Dir.W, Dir.NW])
board.add_word(1, 3, [Dir.N, Dir.NW, Dir.W, Dir.NW, Dir.NE, Dir.S, Dir.E])
board.add_word(1, 0, [Dir.N, Dir.W, Dir.E])

print(board)
print("------")
print(BoardSerializer.from_base64(BoardSerializer.to_base64(board)))
