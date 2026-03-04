from make_lablist import Node

# Create root node
n = Node(0, "Grad", None, None, None, "Faculty", "http://example")
assert n.depth() == 0
assert n.url() == "http://example"

r = n.row()
# Expect tuple of 7 elements: depth, root, child1, child2, child3, current, url
assert isinstance(r, tuple), type(r)
assert len(r) == 7, f"row length is {len(r)}"
assert r[0] == 0
assert r[1] == "Grad"
assert r[2] is None and r[3] is None and r[4] is None
assert r[5] == "Faculty"
assert r[6] == "http://example"

# Create child
c = n.child("Lab", "http://lab")
assert c.depth() == 1
cr = c.row()
assert len(cr) == 7
assert cr[5] == "Lab"

print("OK: Node behavior checks passed")
