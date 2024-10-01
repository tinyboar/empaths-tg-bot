# distributions.py

POSITIONS_MAP = {
    16: [
        [None, 1, 2, 3, 4],
        [16, None, None, None, None, None, 5],
        [15, None, None, None, None, None, 6],
        [14, None, None, None, None, None, 7],
        [13, None, None, None, None, None, 8],
        [None, 12, 11, 10, 9],
    ],
    15: [
        [None, 1, 2, 3, 4],
        [15, None, None, None, None, None, 5],
        [14, None, None, None, None, None, 6],
        [13, None, None, None, None, None, 7],
        [12, None, None, None, None, None, 8],
        [None, None, 11, 10, 9],
    ],
    14: [
        [None, 1, 2, 3],
        [14, None, None, None, None, 4],
        [13, None, None, None, None, 5],
        [12, None, None, None, None, 6],
        [11, None, None, None, None, 7],
        [None, 10, 9, 8],
    ],
    13: [
        [None, 1, 2, 3],
        [13, None, None, None, None, 4],
        [12, None, None, None, None, 5],
        [11, None, None, None, None, 6],
        [10, None, None, None, None, 7],
        [None, None, 9, 8],
    ],
    12: [
        [None, 1, 2, 3],
        [12, None, None, None, 4],
        [11, None, None, None, 5],
        [10, None, None, None, 6],
        [None, 9, 8, 7]
    ],
    11: [
        [None, 1, 2, 3],
        [11, None, None, None, None, 4],
        [10, None, None, None, None, 5],
        [9, None, None, None, None, 6],
        [None, None, 8, 7]
    ],
    10: [
        [None, 1, 2],
        [10, None, None, 3],
        [9, None, None, 4],
        [8, None, None, 5],
        [None, 7, 6]
    ],
    9: [
        [None, 1, 2, 3],
        [9, None, None, None, 3],
        [8, None, None, None, 4],
        [None, 7, 6, 5],
    ],
    8: [
        [None, 1, 2],
        [8, None, None, 3],
        [7, None, None, 4],
        [None, 5, 6],
    ],
    7: [
        [None, 1, 2],
        [7, None, None, 3],
        [6, None, None, 4],
        [None, None, 5],
    ],
}
