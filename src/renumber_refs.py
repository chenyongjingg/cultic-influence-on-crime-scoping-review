#!/usr/bin/env python3
"""Turn citation keys into Vancouver numbers by order of first appearance.

The text carries stable keys ({tricco}, {dayan,smirnova}); numbers are derived here.
That way reordering a paragraph cannot silently leave the reference list out of step
with the text, and two failures are made impossible rather than checked-for
afterwards: a key with no reference, and a reference that nothing cites.

Input : manuscript_filled.md (keys, placeholders already substituted)
Output: manuscript_numbered.md (numbers in text, ordered reference list)
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(src="out/manuscript/manuscript_filled.md",
         dst="out/manuscript/manuscript_numbered.md"):
    md = io.open(os.path.join(ROOT, src), encoding="utf8").read()
    head, refblock = md.split("\n## References\n", 1)
    refblock, tail = refblock.split("\n## Figures", 1)
    tail = "\n## Figures" + tail

    # Reference strings come from a canonical map (key -> formatted citation), not
    # from parsing the current block: once the list is renumbered, the block no
    # longer says which key a number belongs to.
    keys = json.load(io.open(os.path.join(ROOT, "out", "data", "reference_strings.json"),
                             encoding="utf8"))

    # order of first appearance
    order, seen = [], set()
    for m in re.finditer(r"\{([a-z0-9,]+)\}", head):
        for k in m.group(1).split(","):
            if k not in seen:
                seen.add(k); order.append(k)

    missing_ref = [k for k in order if k not in keys]
    uncited = [k for k in keys if k not in seen]
    if missing_ref:
        sys.exit("keys with no reference: %s" % missing_ref)
    if uncited:
        sys.exit("references never cited: %s" % uncited)

    num = {k: i + 1 for i, k in enumerate(order)}

    def repl(m):
        nums = sorted(num[k] for k in m.group(1).split(","))
        return "[" + ",".join(str(n) for n in nums) + "]"

    head2 = re.sub(r"\{([a-z0-9,]+)\}", repl, head)

    lines = ["## References", ""]
    for k in order:
        lines.append("%d. %s" % (num[k], keys[k]))
    out = head2.rstrip() + "\n\n" + "\n".join(lines) + "\n" + tail

    io.open(os.path.join(ROOT, dst), "w", encoding="utf8").write(out)
    print("cited keys: %d, references: %d" % (len(order), len(keys)))
    for k in order:
        print("  [%2d] %-12s %s" % (num[k], k, keys[k][:80]))


if __name__ == "__main__":
    main()
