# Reuse of 2x2 results (mesh3x3; pipeline/reuse.py)

REUSED = golden equal to 2x2 after whitespace normalisation, or Yosys-equivalent, AND byte-identical prompt. Equivalence negative control (2x2 one-shot encoder vs golden) equivalent: False. Wrappers (not golden, never prompted): none.

REUSED 33, NEW 1: top_3x3_router

| module | status | why | golden sha256 raw (2x2 / study) | normalised (2x2 / study) | equivalent | prompt sha256 (2x2 / study) |
|---|---|---|---|---|---|---|
| dff_synch_reset | REUSED | whitespace-identical golden, identical prompt | c85cf10a0ede / c85cf10a0ede | d7a2f71eeb82 / d7a2f71eeb82 | - | 80cc207aec65 / 80cc207aec65 |
| dff_synch_set | REUSED | whitespace-identical golden, identical prompt | c087d00e7fdf / c087d00e7fdf | 549cb42975cc / 549cb42975cc | - | bba7d7b23f73 / bba7d7b23f73 |
| dff_asynch_clr | REUSED | whitespace-identical golden, identical prompt | eb2859b11efd / eb2859b11efd | 781122d52179 / 781122d52179 | - | 45f4e6761832 / 45f4e6761832 |
| irs | REUSED | whitespace-identical golden, identical prompt | 336845c14afc / 336845c14afc | 2cd65dd1f8dc / 2cd65dd1f8dc | - | 7a283915bda9 / 7a283915bda9 |
| register_32bit | REUSED | whitespace-identical golden, identical prompt | 8093f8f2fa0d / 8093f8f2fa0d | ec811a261eac / ec811a261eac | - | bdfc3046737f / bdfc3046737f |
| asynch_comparator | REUSED | Yosys-equivalent golden, mutant rejected, identical prompt | b4557b38aed8 / 3a2fefc860f8 | 6300b710b3de / 60d3598da1a1 | True | 83013239423e / 83013239423e |
| jk_ff | REUSED | whitespace-identical golden, identical prompt | 48b73e3c5446 / 48b73e3c5446 | fd82422b2839 / fd82422b2839 | - | c46252d5627f / c46252d5627f |
| gray_mod6 | REUSED | Yosys-equivalent golden, mutant rejected, identical prompt | 573d5d4a73db / 20d7ec860b2d | b2947dfa6bc4 / a1f89292a4f3 | True | ed9570d5a7f0 / ed9570d5a7f0 |
| memory | REUSED | whitespace-identical golden, identical prompt | 7e2cedb766e1 / 7ee1357d16eb | 271512d24e7b / 271512d24e7b | - | 90f838321434 / 90f838321434 |
| router_fifo | REUSED | whitespace-identical golden, identical prompt | 0161b571a2ee / aa139fa62865 | 5e6e81142a5a / 5e6e81142a5a | - | 045150e5c0e5 / 045150e5c0e5 |
| routing_algo_mesh | REUSED | whitespace-identical golden, identical prompt | 0d99bf49e30d / 0d99bf49e30d | f4c9fcab3a24 / f4c9fcab3a24 | - | d9de48b5cb4d / d9de48b5cb4d |
| ip_chnl | REUSED | whitespace-identical golden, identical prompt | 26262ddeb248 / 26262ddeb248 | d022f0f0d49e / d022f0f0d49e | - | 4ed6bac1e4aa / 4ed6bac1e4aa |
| ip_link | REUSED | whitespace-identical golden, identical prompt | 274ed86db1b9 / abf70c12af76 | 4b97adad389b / 4b97adad389b | - | d60d8854c375 / d60d8854c375 |
| mux | REUSED | whitespace-identical golden, identical prompt | 8ff302cff244 / 8ff302cff244 | 48c3d71c49a0 / 48c3d71c49a0 | - | 586af1223990 / 586af1223990 |
| register_1bit | REUSED | whitespace-identical golden, identical prompt | 6882d711c809 / 6882d711c809 | ad8ff780bcf5 / ad8ff780bcf5 | - | 38d66ebf85ec / 38d66ebf85ec |
| register_4bit | REUSED | whitespace-identical golden, identical prompt | d914413e52af / d914413e52af | cceb527df721 / cceb527df721 | - | 1af39806e45f / 1af39806e45f |
| allot_vc | REUSED | whitespace-identical golden, identical prompt | c4896489368c / c4896489368c | b06f2e33ac7f / b06f2e33ac7f | - | 6f91064fe085 / 6f91064fe085 |
| demux_16 | REUSED | whitespace-identical golden, identical prompt | 6a566a991a0b / 6a566a991a0b | bd7bb69e9d6f / bd7bb69e9d6f | - | d23006ebac0b / d23006ebac0b |
| encoder | REUSED | whitespace-identical golden, identical prompt | 86d85fcd26a2 / 86d85fcd26a2 | ea06feb908d6 / ea06feb908d6 | - | 330fb1e746f8 / 330fb1e746f8 |
| falling_edge_pulse_generator | REUSED | whitespace-identical golden, identical prompt | 2ecd238beb95 / 2ecd238beb95 | ddf42dd9d583 / ddf42dd9d583 | - | aa2af1e467cd / aa2af1e467cd |
| priority_encoder | REUSED | whitespace-identical golden, identical prompt | 607713b8356a / 607713b8356a | a8d37213821e / a8d37213821e | - | 9625a7c0bd49 / 9625a7c0bd49 |
| rr_arbiter | REUSED | whitespace-identical golden, identical prompt | 0f4368f5eabd / 0f4368f5eabd | f6fcda4be398 / f6fcda4be398 | - | 49ea53fcc506 / 49ea53fcc506 |
| round_robin_req | REUSED | whitespace-identical golden, identical prompt | a1875de3ef42 / a1875de3ef42 | 07c4e126d2ef / 07c4e126d2ef | - | 392929ca1323 / 392929ca1323 |
| dff_synch_clr | REUSED | whitespace-identical golden, identical prompt | 594b5f8e077e / 594b5f8e077e | 87f011f32c50 / 87f011f32c50 | - | 5055cd51a6f4 / 5055cd51a6f4 |
| rr_comb_new | REUSED | whitespace-identical golden, identical prompt | 45bf1b0933d5 / 45bf1b0933d5 | ab400b6e0e0d / ab400b6e0e0d | - | 74b024604d85 / 74b024604d85 |
| op_core | REUSED | whitespace-identical golden, identical prompt | 4c843a3d23eb / 4c843a3d23eb | fd1b27b3dc44 / fd1b27b3dc44 | - | 7d8dabc2dfa5 / 7d8dabc2dfa5 |
| final_op_data | REUSED | whitespace-identical golden, identical prompt | d0a8a9412397 / d0a8a9412397 | c590ebd3580c / c590ebd3580c | - | f0c39aceb960 / f0c39aceb960 |
| op_data_path | REUSED | whitespace-identical golden, identical prompt | 2a5e65a7ed2d / 2a5e65a7ed2d | 54736936e759 / 54736936e759 | - | c11dcda0dbfb / c11dcda0dbfb |
| op_link1 | REUSED | whitespace-identical golden, identical prompt | dfa10e5e4fe7 / dfa10e5e4fe7 | 2cd40ca7a57c / 2cd40ca7a57c | - | 57c86f424310 / 57c86f424310 |
| op_link2 | REUSED | whitespace-identical golden, identical prompt | 7602dfdfff76 / 7602dfdfff76 | 3027187887c4 / 3027187887c4 | - | 75e74e260f66 / 75e74e260f66 |
| op_link3 | REUSED | whitespace-identical golden, identical prompt | d9d8955b64e5 / d9d8955b64e5 | ca17f43b64cc / ca17f43b64cc | - | 6c18e4b78953 / 6c18e4b78953 |
| op_link4 | REUSED | whitespace-identical golden, identical prompt | ae5d19849a99 / ae5d19849a99 | 215a7d176e4f / 215a7d176e4f | - | 7d510955a77b / 7d510955a77b |
| top_module | REUSED | whitespace-identical golden, identical prompt | 50676eb017b9 / 50676eb017b9 | 79e1ffb367db / 79e1ffb367db | - | c97c02ea4fe1 / c97c02ea4fe1 |
| top_3x3_router | NEW | no 2x2 module of this name | - / dd19672dac96 | - / c97ea26999a3 | - | - / 6b1b7aba73a8 |

Full hashes: reports/reuse.json.
