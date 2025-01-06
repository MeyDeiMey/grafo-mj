# graph/node.py

class Node:
    def __init__(self, word: str):
        self.word = word

    def __repr__(self):
        return f"Node({self.word})"

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.word == other.word
        return False

    def __hash__(self):
        return hash(self.word)
