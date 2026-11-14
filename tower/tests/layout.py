"""The choice of the layout of a program by the price (language 5 on the chain), made on the chain itself (25.7.3.4; it was l5.chain_cost and l5.replace_layout over the Python
references): the serial layout of a text of language 3 or the packed one (the word `pack` before the text). The cost is the tuple (rows, layers, bits, ticks) of
golden_programs.cost_of (counted from the texts of language 2 which l3c and l3p write) and the ticks of the dearest run of the image chain.build makes; the price is
golden_programs.price (32 rows + 32 layers + bits + 64 ticks). The lower languages do not know the price, the word `pack` is all they get.
chain_cost(src, inputs) -> (Cost, [(rc, output) of every input])    replace_layout(src, inputs) -> Choice(index, prices, program text)"""
import os
import sys
from collections import namedtuple

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain
import golden_programs

Cost = namedtuple('Cost', 'rows layers bits ticks')
Choice = namedtuple('Choice', 'index prices program')


def price(c):
    """One number from the cost: the weighted sum of golden_programs.PRICE_W."""
    return golden_programs.price(c[:3], c.ticks)


def chain_cost(src, inputs=(b'',), limit=2 * 10 ** 8):
    """The cost of a text of language 3 on the chain, in its own layout (the word `pack` first or not): rows, layers, bits of its blocks, ticks of the dearest of the runs on
    `inputs` (the checked emulator). Returns (Cost, [(rc, output) of every input])."""
    text = src.decode('latin-1') if isinstance(src, bytes) else src
    packed = chain.is_pack(text)
    counted = golden_programs.cost_of(text.encode('latin-1'), packed, False)
    if counted is None:
        raise ValueError('the chain: the planner does not take the text')
    img, P = chain.build(text)
    ticks, outs = 0, []
    for inp in inputs:
        r = chain.run_image(img, P, stdin=inp, checked=True, limit=limit)
        if r.ticks is None or r.ticks >= limit:
            raise ValueError('the run does not end')
        ticks = max(ticks, r.ticks)
        outs.append((r.rc, r.out))
    return Cost(*counted, ticks), outs


def replace_layout(src, inputs=(b'',)):
    """The cheaper layout of a program: the serial one or the packed one. Both must give the same result on every input of `inputs` (else ValueError). Returns
    Choice(index, prices, text of the chosen layout); 0 is serial, 1 packed (serial when equal)."""
    text = (src.decode('latin-1') if isinstance(src, bytes) else src).removeprefix('pack\n')
    made = [chain_cost(t, inputs) for t in (text, 'pack\n' + text)]
    if made[0][1] != made[1][1]:
        raise ValueError('the layouts give different results')
    prices = [price(c) for c, _ in made]
    i = prices.index(min(prices))
    return Choice(i, prices, ('pack\n' if i else '') + text)
