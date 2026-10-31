# Reuse of 2x2 results (ni; pipeline/reuse.py)

REUSED = golden equal to 2x2 after whitespace normalisation, or Yosys-equivalent, AND byte-identical prompt. Equivalence negative control (2x2 one-shot encoder vs golden) equivalent: False. Wrappers (not golden, never prompted): ni_pair.

REUSED 5, NEW 4: rp1, new1, depack, nidepack

| module | status | why | golden sha256 raw (2x2 / study) | normalised (2x2 / study) | equivalent | prompt sha256 (2x2 / study) |
|---|---|---|---|---|---|---|
| asynch_comparator | REUSED | whitespace-identical golden, identical prompt | b4557b38aed8 / b4557b38aed8 | 6300b710b3de / 6300b710b3de | - | 83013239423e / 83013239423e |
| jk_ff | REUSED | whitespace-identical golden, identical prompt | 48b73e3c5446 / 48b73e3c5446 | fd82422b2839 / fd82422b2839 | - | c46252d5627f / c46252d5627f |
| gray_mod6 | REUSED | whitespace-identical golden, identical prompt | 573d5d4a73db / 573d5d4a73db | b2947dfa6bc4 / b2947dfa6bc4 | - | ed9570d5a7f0 / ed9570d5a7f0 |
| memory | REUSED | whitespace-identical golden, identical prompt | 7e2cedb766e1 / 7e2cedb766e1 | 271512d24e7b / 271512d24e7b | - | 90f838321434 / 90f838321434 |
| router_fifo | REUSED | whitespace-identical golden, identical prompt | 0161b571a2ee / 0161b571a2ee | 5e6e81142a5a / 5e6e81142a5a | - | 045150e5c0e5 / 045150e5c0e5 |
| rp1 | NEW | no 2x2 module of this name | - / 4f89d6f88ad2 | - / 00c35345d099 | - | - / e733a50918e2 |
| new1 | NEW | no 2x2 module of this name | - / 46951ab4b042 | - / 622f7b5503aa | - | - / 571d0bc3243c |
| depack | NEW | no 2x2 module of this name | - / 06a8a1732cb9 | - / 8ecb8f8fe21e | - | - / aa978f6f43d3 |
| nidepack | NEW | no 2x2 module of this name | - / 63efea876e75 | - / 783a13621225 | - | - / e0af6ceb87e1 |

Full hashes: reports/reuse.json.
