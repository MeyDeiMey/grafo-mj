# graph/node.py

class Node:
    def __init__(self, word: str):
        self.word = word

    def __repr__(self):
        return f"Node({self.word})"

    def __eq__(self, other):
        return isinstance(other, Node) and other.word == self.word

    def __hash__(self):
        return hash(self.word)
