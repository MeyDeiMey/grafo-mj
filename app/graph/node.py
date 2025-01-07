# app/graph/node.py

import logging

logger = logging.getLogger(__name__)

class Node:
    def __init__(self, word: str):
        if not isinstance(word, str):
            logger.error(f"Invalid type for word: {type(word)}. Word must be a string.")
            raise ValueError("Word must be a string")
        self.word = word
        logger.info(f"Node created with word: {self.word}")

    def __repr__(self):
        return f"Node({self.word})"

    def __eq__(self, other):
        if isinstance(other, Node):
            is_equal = self.word == other.word
            logger.debug(f"Comparing Node({self.word}) with Node({other.word}): {is_equal}")
            return is_equal
        logger.debug(f"Comparing Node({self.word}) with non-Node object: False")
        return False

    def __hash__(self):
        try:
            word_hash = hash(self.word)
            logger.debug(f"Hash for Node({self.word}): {word_hash}")
            return word_hash
        except Exception as e:
            logger.error(f"Error hashing Node({self.word}): {e}")
            raise e
