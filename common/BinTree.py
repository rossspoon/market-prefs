#Binary Tree node
class Node:
    def __init__(self, val):
        self.left = None
        self.right = None
        self.val = str(val)


    def print_tree(self,  level=0):
        next_lev = level+1
        # go right
        if self.right:
            self.right.print_tree(level=next_lev)

        # visit this node
        pad = '\t' * level;
        print(pad, self.val)

        #go left
        if self.left:
            self.left.print_tree(level=next_lev)
