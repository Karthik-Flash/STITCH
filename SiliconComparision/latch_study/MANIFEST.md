# Handoff manifest

Every delivered file is listed with its repository-relative source and SHA-256. This inventory excludes MANIFEST.md itself because embedding its final hash would be self-referential.

## Toolchain and verification

- Yosys: 0.69+71 (matched STITCH_SET4_OSSCAD suite).
- A_original: expected abort on mesh2x2, mesh3x3, and mpsoc with `Multiple edge sensitive events found for this signal`. 
- A1_original_synthesisable latches: mesh2x2 2,880; mesh3x3 6,480; mpsoc 269.
- B_repaired_golden latches: mesh2x2 0; mesh3x3 0; mpsoc 122.
- C_repaired_stitch latches: mesh2x2 0; mesh3x3 0; mpsoc 122.
- All A1, B, and C tops synthesize successfully.

## C provenance

- Model: deepseek-coder:6.7b; condition: sem_esc_restart_v3; replicate: 2.
- Compose record: phase3/results/phase3_run/compose_results.jsonl; SHA-256: 7a7895a1e9da52b3fc6a5f960e63ad0efb6f24453298f3f7653690edbae3375c.
- The eight real leaves spliced into C are sign-off clean; mesh2x2, mesh3x3, and mpsoc top-level synthesis passed.
- The three seeded leaf artifacts are included for completeness; riscv_alu_flags is not sign-off clean and is not instantiated in these designs.

## A1 versus B (name-only diff)

- mesh2x2, mesh3x3: register_32bit, register_4bit.
- mpsoc: Address_select, execute_mux, mem_wb_mux, mux3, MuxPC, register_32bit, register_4bit.
- register_1bit is the same golden replacement in A1 and B.

## File inventory

| Handoff file | Source path | SHA-256 |
|---|---|---|
| `A1_original_synthesisable/mesh2x2/__repaired_register_1bit.v` | `phase3/tasks/register_1bit/golden.v` | `6882d711c809e90728c66a9ecc6696bbdc81416f312522b6ad70f0e1c8aef4dd` |
| `A1_original_synthesisable/mesh2x2/allot_vc.v` | `phase3/designs/mesh2x2_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `A1_original_synthesisable/mesh2x2/asynch_comparator.v` | `phase3/designs/mesh2x2_ref/asynch_comparator.v` | `b4557b38aed8ef3881524b9b7d09d9d432bcef363bb05ad2942eb8bcc25caaf1` |
| `A1_original_synthesisable/mesh2x2/demux_16.v` | `phase3/designs/mesh2x2_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `A1_original_synthesisable/mesh2x2/dff_asynch_clr.v` | `phase3/designs/mesh2x2_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `A1_original_synthesisable/mesh2x2/dff_synch_clr.v` | `phase3/designs/mesh2x2_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `A1_original_synthesisable/mesh2x2/dff_synch_reset.v` | `phase3/designs/mesh2x2_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `A1_original_synthesisable/mesh2x2/dff_synch_set.v` | `phase3/designs/mesh2x2_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `A1_original_synthesisable/mesh2x2/encoder.v` | `phase3/designs/mesh2x2_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `A1_original_synthesisable/mesh2x2/falling_edge_pulse_generator.v` | `phase3/designs/mesh2x2_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `A1_original_synthesisable/mesh2x2/fop.v` | `phase3/designs/mesh2x2_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `A1_original_synthesisable/mesh2x2/gray_mod6.v` | `phase3/designs/mesh2x2_ref/gray_mod6.v` | `573d5d4a73db10d594b32a6a179121868c330ec2b35de020081b6b8ca6c87002` |
| `A1_original_synthesisable/mesh2x2/ip_chnl.v` | `phase3/designs/mesh2x2_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `A1_original_synthesisable/mesh2x2/ip_link.v` | `phase3/designs/mesh2x2_ref/ip_link.v` | `274ed86db1b94f6da7f0b213d7cf89a839a67942506d351511d07b97f5f53501` |
| `A1_original_synthesisable/mesh2x2/IRS.v` | `phase3/designs/mesh2x2_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `A1_original_synthesisable/mesh2x2/jk_ff.v` | `phase3/designs/mesh2x2_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `A1_original_synthesisable/mesh2x2/memory.v` | `phase3/designs/mesh2x2_ref/memory.v` | `7e2cedb766e1e73831dca04b00ffb88886b022d344ce44201dcee52fa020d6cc` |
| `A1_original_synthesisable/mesh2x2/mesh_router2x2.v` | `phase3/designs/mesh2x2_ref/mesh_router2x2.v` | `8845909cdd62829c46cb60e3c8245911cc507cd96ab3c30aca34f942191f5c57` |
| `A1_original_synthesisable/mesh2x2/mux.v` | `phase3/designs/mesh2x2_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `A1_original_synthesisable/mesh2x2/op_core.v` | `phase3/designs/mesh2x2_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `A1_original_synthesisable/mesh2x2/op_data_path.v` | `phase3/designs/mesh2x2_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `A1_original_synthesisable/mesh2x2/op_link1.v` | `phase3/designs/mesh2x2_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `A1_original_synthesisable/mesh2x2/op_link2.v` | `phase3/designs/mesh2x2_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `A1_original_synthesisable/mesh2x2/op_link3.v` | `phase3/designs/mesh2x2_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `A1_original_synthesisable/mesh2x2/op_link4.v` | `phase3/designs/mesh2x2_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `A1_original_synthesisable/mesh2x2/priority_encoder.v` | `phase3/designs/mesh2x2_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `A1_original_synthesisable/mesh2x2/register_1bit.v` | `phase3/designs/mesh2x2_ref/register_1bit.v (compose.py stripped: register_1bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `A1_original_synthesisable/mesh2x2/register_32bit.v` | `phase3/designs/mesh2x2_ref/register_32bit.v` | `25918dc924e9af5628cbb09d70df8be153aeca5a170a4e7a5e920e8615470f4c` |
| `A1_original_synthesisable/mesh2x2/register_4bit.v` | `phase3/designs/mesh2x2_ref/register_4bit.v` | `514bef71c2972956fdeade04b4823d140cf6f8261f21f5f8ab5308758350557e` |
| `A1_original_synthesisable/mesh2x2/round_robin_req.v` | `phase3/designs/mesh2x2_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `A1_original_synthesisable/mesh2x2/router_fifo.v` | `phase3/designs/mesh2x2_ref/router_fifo.v` | `0161b571a2eecf0fe0749887008d4ebfc4bd624cfd1af6e025acdb96a4fc1224` |
| `A1_original_synthesisable/mesh2x2/routing_algo_mesh.v` | `phase3/designs/mesh2x2_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `A1_original_synthesisable/mesh2x2/rr_arbiter.v` | `phase3/designs/mesh2x2_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `A1_original_synthesisable/mesh2x2/rr_comb_new.v` | `phase3/designs/mesh2x2_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `A1_original_synthesisable/mesh2x2/top_module.v` | `phase3/designs/mesh2x2_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `A1_original_synthesisable/mesh3x3/__repaired_register_1bit.v` | `phase3/tasks/register_1bit/golden.v` | `6882d711c809e90728c66a9ecc6696bbdc81416f312522b6ad70f0e1c8aef4dd` |
| `A1_original_synthesisable/mesh3x3/allot_vc.v` | `phase3/designs/mesh3x3_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `A1_original_synthesisable/mesh3x3/asynch_comparator.v` | `phase3/designs/mesh3x3_ref/asynch_comparator.v` | `3a2fefc860f8f880266edadd89a758609f94884462c1daddda8d371993e4a649` |
| `A1_original_synthesisable/mesh3x3/demux_16.v` | `phase3/designs/mesh3x3_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `A1_original_synthesisable/mesh3x3/dff_asynch_clr.v` | `phase3/designs/mesh3x3_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `A1_original_synthesisable/mesh3x3/dff_synch_clr.v` | `phase3/designs/mesh3x3_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `A1_original_synthesisable/mesh3x3/dff_synch_reset.v` | `phase3/designs/mesh3x3_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `A1_original_synthesisable/mesh3x3/dff_synch_set.v` | `phase3/designs/mesh3x3_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `A1_original_synthesisable/mesh3x3/encoder.v` | `phase3/designs/mesh3x3_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `A1_original_synthesisable/mesh3x3/falling_edge_pulse_generator.v` | `phase3/designs/mesh3x3_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `A1_original_synthesisable/mesh3x3/fop.v` | `phase3/designs/mesh3x3_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `A1_original_synthesisable/mesh3x3/gray_mod6.v` | `phase3/designs/mesh3x3_ref/gray_mod6.v` | `20d7ec860b2dbee42d07ee79b22f9cefe57940e5a7c808728031f215c86b4165` |
| `A1_original_synthesisable/mesh3x3/ip_chnl.v` | `phase3/designs/mesh3x3_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `A1_original_synthesisable/mesh3x3/ip_link.v` | `phase3/designs/mesh3x3_ref/ip_link.v` | `abf70c12af7667913388266ea4b0743fc7c117f236855eff7b59805795d91914` |
| `A1_original_synthesisable/mesh3x3/IRS.v` | `phase3/designs/mesh3x3_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `A1_original_synthesisable/mesh3x3/jk_ff.v` | `phase3/designs/mesh3x3_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `A1_original_synthesisable/mesh3x3/memory.v` | `phase3/designs/mesh3x3_ref/memory.v` | `7ee1357d16ebbdc27de1ff9af6aa38b9ce4e2f63d5775ae1858b50084dd9f9c7` |
| `A1_original_synthesisable/mesh3x3/mesh_router3x3.v` | `phase3/designs/mesh3x3_ref/mesh_router3x3.v` | `dd19672dac96e7438a3495e90e94c4a00b5b73a153f7c9d5f2c994a00b2a37df` |
| `A1_original_synthesisable/mesh3x3/mux.v` | `phase3/designs/mesh3x3_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `A1_original_synthesisable/mesh3x3/op_core.v` | `phase3/designs/mesh3x3_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `A1_original_synthesisable/mesh3x3/op_data_path.v` | `phase3/designs/mesh3x3_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `A1_original_synthesisable/mesh3x3/op_link1.v` | `phase3/designs/mesh3x3_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `A1_original_synthesisable/mesh3x3/op_link2.v` | `phase3/designs/mesh3x3_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `A1_original_synthesisable/mesh3x3/op_link3.v` | `phase3/designs/mesh3x3_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `A1_original_synthesisable/mesh3x3/op_link4.v` | `phase3/designs/mesh3x3_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `A1_original_synthesisable/mesh3x3/priority_encoder.v` | `phase3/designs/mesh3x3_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `A1_original_synthesisable/mesh3x3/register_1bit.v` | `phase3/designs/mesh3x3_ref/register_1bit.v (compose.py stripped: register_1bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `A1_original_synthesisable/mesh3x3/register_32bit.v` | `phase3/designs/mesh3x3_ref/register_32bit.v` | `25918dc924e9af5628cbb09d70df8be153aeca5a170a4e7a5e920e8615470f4c` |
| `A1_original_synthesisable/mesh3x3/register_4bit.v` | `phase3/designs/mesh3x3_ref/register_4bit.v` | `514bef71c2972956fdeade04b4823d140cf6f8261f21f5f8ab5308758350557e` |
| `A1_original_synthesisable/mesh3x3/round_robin_req.v` | `phase3/designs/mesh3x3_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `A1_original_synthesisable/mesh3x3/router_fifo.v` | `phase3/designs/mesh3x3_ref/router_fifo.v` | `aa139fa628650c6a8a65efeec1df5f01492d4b6b42fe335644171871c03cb425` |
| `A1_original_synthesisable/mesh3x3/routing_algo_mesh.v` | `phase3/designs/mesh3x3_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `A1_original_synthesisable/mesh3x3/rr_arbiter.v` | `phase3/designs/mesh3x3_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `A1_original_synthesisable/mesh3x3/rr_comb_new.v` | `phase3/designs/mesh3x3_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `A1_original_synthesisable/mesh3x3/top_module.v` | `phase3/designs/mesh3x3_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `A1_original_synthesisable/mpsoc/__repaired_register_1bit.v` | `phase3/tasks/register_1bit/golden.v` | `6882d711c809e90728c66a9ecc6696bbdc81416f312522b6ad70f0e1c8aef4dd` |
| `A1_original_synthesisable/mpsoc/adder.v` | `phase3/designs/mpsoc_ref/adder.v` | `f21e095778df9d4e649f16ccba75eec0703640cff2dd0eba914818b2ab98b1bb` |
| `A1_original_synthesisable/mpsoc/address_fetch.v` | `phase3/designs/mpsoc_ref/address_fetch.v` | `c2954b3607895e48a9467be93f09c0c295f399b652ac133f9c01b2ba9e030fde` |
| `A1_original_synthesisable/mpsoc/Address_select.v` | `phase3/designs/mpsoc_ref/Address_select.v` | `4dd66aba54acc0cd1fe3120d21182d7fb69ad08373c77e8b967d1113b87d8c40` |
| `A1_original_synthesisable/mpsoc/allot_vc.v` | `phase3/designs/mpsoc_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `A1_original_synthesisable/mpsoc/ALU.v` | `phase3/designs/mpsoc_ref/ALU.v` | `249a175643ba65cf816fd67c1e0de4dd2c1f0be54705e09c8cad2e6fac9edfef` |
| `A1_original_synthesisable/mpsoc/asynch_comparator.v` | `phase3/designs/mpsoc_ref/asynch_comparator.v` | `b4557b38aed8ef3881524b9b7d09d9d432bcef363bb05ad2942eb8bcc25caaf1` |
| `A1_original_synthesisable/mpsoc/Branch_Cal.v` | `phase3/designs/mpsoc_ref/Branch_Cal.v` | `b7907ae9eddcd35b474e75071c73b38d9930d8d5157d4f0d61c64a2f888c0453` |
| `A1_original_synthesisable/mpsoc/Branch_comparator.v` | `phase3/designs/mpsoc_ref/Branch_comparator.v` | `866844561638a0de009c2ee44c059a5cbee4fe157161088e8b4191d1ff508b5f` |
| `A1_original_synthesisable/mpsoc/control.v` | `phase3/designs/mpsoc_ref/control.v` | `3b639fc36a6a321dacc829569e34a4b9bee230d0564b94a361c6338ef7e6de1c` |
| `A1_original_synthesisable/mpsoc/Data_mem.v` | `phase3/designs/mpsoc_ref/Data_mem.v` | `2ffdeb7e313461cd9f1400a13c98fa3365638016a4b98a9cbde426b43c390035` |
| `A1_original_synthesisable/mpsoc/Decoder.v` | `phase3/designs/mpsoc_ref/Decoder.v` | `3afd37a82ce8b58eae162682214d979db57f82aae78b3b01ee8c65ef22dab8f8` |
| `A1_original_synthesisable/mpsoc/demux_16.v` | `phase3/designs/mpsoc_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `A1_original_synthesisable/mpsoc/depack.v` | `phase3/designs/mpsoc_ref/depack.v` | `06a8a1732cb9f57969f7226139d6b9437366c7095af917375a79edf8a57898ca` |
| `A1_original_synthesisable/mpsoc/dff_asynch_clr.v` | `phase3/designs/mpsoc_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `A1_original_synthesisable/mpsoc/dff_synch_clr.v` | `phase3/designs/mpsoc_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `A1_original_synthesisable/mpsoc/dff_synch_reset.v` | `phase3/designs/mpsoc_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `A1_original_synthesisable/mpsoc/dff_synch_set.v` | `phase3/designs/mpsoc_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `A1_original_synthesisable/mpsoc/encoder.v` | `phase3/designs/mpsoc_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `A1_original_synthesisable/mpsoc/ex_mem.v` | `phase3/designs/mpsoc_ref/ex_mem.v` | `fa69c8cd4a2da2f3714e62150b69f3395caae8dda91b3d2fffb12ed3839173bd` |
| `A1_original_synthesisable/mpsoc/execute.v` | `phase3/designs/mpsoc_ref/execute.v` | `0eed9f7a017b6806cbc4a589c894b5986c59434de6311dc0f7ed5f0155f9503d` |
| `A1_original_synthesisable/mpsoc/execution_unit.v` | `phase3/designs/mpsoc_ref/execution_unit.v` | `f43048e2060ec6e4fe254bc531a894d292d057c5baf771fb4d89ee28dc0806b5` |
| `A1_original_synthesisable/mpsoc/falling_edge_pulse_generator.v` | `phase3/designs/mpsoc_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `A1_original_synthesisable/mpsoc/fop.v` | `phase3/designs/mpsoc_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `A1_original_synthesisable/mpsoc/forwarding_unit.v` | `phase3/designs/mpsoc_ref/forwarding_unit.v` | `a167a149221b77e78099e3dd0efce0f40605ac1532ab8f43b25ffd3945510c34` |
| `A1_original_synthesisable/mpsoc/gray_mod6.v` | `phase3/designs/mpsoc_ref/gray_mod6.v` | `573d5d4a73db10d594b32a6a179121868c330ec2b35de020081b6b8ca6c87002` |
| `A1_original_synthesisable/mpsoc/id_ex.v` | `phase3/designs/mpsoc_ref/id_ex.v` | `ff139e355ee8c5ee7a869c151f59e1f0049d6d5140a7c7d927d7c20d30a9fae8` |
| `A1_original_synthesisable/mpsoc/if_id.v` | `phase3/designs/mpsoc_ref/if_id.v` | `710fda6c552b596adc9d065d37e8aceb9f7a8c1df193b9f1e1a395a212322398` |
| `A1_original_synthesisable/mpsoc/IFU.v` | `phase3/designs/mpsoc_ref/IFU.v` | `1695f2216c8b00fa500c728506fc468fd19224de3e911327ffb709d79ce330e4` |
| `A1_original_synthesisable/mpsoc/inst_mem.v` | `phase3/designs/mpsoc_ref/inst_mem.v` | `248fb494e7ed31bbfd6a45d029df047ed854bbc0c0e123331dd39ae933379c98` |
| `A1_original_synthesisable/mpsoc/Inst_mem_integrated.v` | `phase3/designs/mpsoc_ref/Inst_mem_integrated.v` | `12ec8f623b331421693493ba9ebe5bd9bd7c60d42247bcee708db0693193c20a` |
| `A1_original_synthesisable/mpsoc/ip_chnl.v` | `phase3/designs/mpsoc_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `A1_original_synthesisable/mpsoc/ip_link.v` | `phase3/designs/mpsoc_ref/ip_link.v` | `274ed86db1b94f6da7f0b213d7cf89a839a67942506d351511d07b97f5f53501` |
| `A1_original_synthesisable/mpsoc/IRS.v` | `phase3/designs/mpsoc_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `A1_original_synthesisable/mpsoc/jk_ff.v` | `phase3/designs/mpsoc_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `A1_original_synthesisable/mpsoc/main.v` | `phase3/designs/mpsoc_ref/main.v` | `6d613298e0ed1488fcd6a88ff3f40afd4aa4bd3c9cfc71c4381970af0806e934` |
| `A1_original_synthesisable/mpsoc/mem_wb.v` | `phase3/designs/mpsoc_ref/mem_wb.v` | `73f5de75f101c7e79c5c00829f53b5ef007ea5ccc681c93163a8ccdfc5746062` |
| `A1_original_synthesisable/mpsoc/mem_wb_mux.v` | `phase3/designs/mpsoc_ref/mem_wb_mux.v` | `43be6242ed1edd5c030e9ce498edf8f38bba73d657bd6c102ba414ed410880ee` |
| `A1_original_synthesisable/mpsoc/memory.v` | `phase3/designs/mpsoc_ref/memory.v` | `7e2cedb766e1e73831dca04b00ffb88886b022d344ce44201dcee52fa020d6cc` |
| `A1_original_synthesisable/mpsoc/mesh_router2x2.v` | `phase3/designs/mpsoc_ref/mesh_router2x2.v` | `8845909cdd62829c46cb60e3c8245911cc507cd96ab3c30aca34f942191f5c57` |
| `A1_original_synthesisable/mpsoc/multiply.v` | `phase3/designs/mpsoc_ref/multiply.v` | `e8ad7ff2591e2c68eb4757b7865919f8d59df53d93edd8d7403d75f2e5a0e92c` |
| `A1_original_synthesisable/mpsoc/mux.v` | `phase3/designs/mpsoc_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `A1_original_synthesisable/mpsoc/mux3.v` | `phase3/designs/mpsoc_ref/mux3.v` | `f1d95d55993057a1efcf52f6eb3a15bbba75cce4eeb0fa75b28eb5db9dc49619` |
| `A1_original_synthesisable/mpsoc/MuxPC.v` | `phase3/designs/mpsoc_ref/MuxPC.v` | `8e92ff841abe331db28145f337b61526c9680403a004b2faf3e676eb75f21f35` |
| `A1_original_synthesisable/mpsoc/new.v` | `phase3/designs/mpsoc_ref/new.v` | `46951ab4b04254af6cf4ff23b4b28aa618c96f4e2719ccf32d66bb3a2c6b4ddd` |
| `A1_original_synthesisable/mpsoc/new_mux.v` | `phase3/designs/mpsoc_ref/new_mux.v` | `c4f2de43161eae5b0494941f967901402a87bc2a528e7ad5deebcc444dc00e87` |
| `A1_original_synthesisable/mpsoc/nidepack.v` | `phase3/designs/mpsoc_ref/nidepack.v` | `63efea876e75da22b067b545bbefacfb9120e5d1957b53d4e7414b37805a3688` |
| `A1_original_synthesisable/mpsoc/op_core.v` | `phase3/designs/mpsoc_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `A1_original_synthesisable/mpsoc/op_data_path.v` | `phase3/designs/mpsoc_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `A1_original_synthesisable/mpsoc/op_link1.v` | `phase3/designs/mpsoc_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `A1_original_synthesisable/mpsoc/op_link2.v` | `phase3/designs/mpsoc_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `A1_original_synthesisable/mpsoc/op_link3.v` | `phase3/designs/mpsoc_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `A1_original_synthesisable/mpsoc/op_link4.v` | `phase3/designs/mpsoc_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `A1_original_synthesisable/mpsoc/priority_encoder.v` | `phase3/designs/mpsoc_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `A1_original_synthesisable/mpsoc/Processor.v` | `phase3/designs/mpsoc_ref/Processor.v` | `f37cc5eac4075a9c5a28d0c972c2658b45518155370526ef398573de0fc8f00e` |
| `A1_original_synthesisable/mpsoc/register_1bit.v` | `phase3/designs/mpsoc_ref/register_1bit.v (compose.py stripped: register_1bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `A1_original_synthesisable/mpsoc/register_32bit.v` | `phase3/designs/mpsoc_ref/register_32bit.v` | `25918dc924e9af5628cbb09d70df8be153aeca5a170a4e7a5e920e8615470f4c` |
| `A1_original_synthesisable/mpsoc/register_4bit.v` | `phase3/designs/mpsoc_ref/register_4bit.v` | `514bef71c2972956fdeade04b4823d140cf6f8261f21f5f8ab5308758350557e` |
| `A1_original_synthesisable/mpsoc/round_robin_req.v` | `phase3/designs/mpsoc_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `A1_original_synthesisable/mpsoc/router_fifo.v` | `phase3/designs/mpsoc_ref/router_fifo.v` | `0161b571a2eecf0fe0749887008d4ebfc4bd624cfd1af6e025acdb96a4fc1224` |
| `A1_original_synthesisable/mpsoc/routing_algo_mesh.v` | `phase3/designs/mpsoc_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `A1_original_synthesisable/mpsoc/rp1.v` | `phase3/designs/mpsoc_ref/rp1.v` | `4f89d6f88ad218b57f9b9540a8cfa86b744bbb9a26080447157b4c6323445871` |
| `A1_original_synthesisable/mpsoc/rr_arbiter.v` | `phase3/designs/mpsoc_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `A1_original_synthesisable/mpsoc/rr_comb_new.v` | `phase3/designs/mpsoc_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `A1_original_synthesisable/mpsoc/stall_unit.v` | `phase3/designs/mpsoc_ref/stall_unit.v` | `b6b40729c82962de3d3d2f3cd61d78ceb0c55ed8d789c47feeb8b5893e78ae95` |
| `A1_original_synthesisable/mpsoc/top_module.v` | `phase3/designs/mpsoc_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `A_original/mesh2x2/allot_vc.v` | `phase3/designs/mesh2x2_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `A_original/mesh2x2/asynch_comparator.v` | `phase3/designs/mesh2x2_ref/asynch_comparator.v` | `b4557b38aed8ef3881524b9b7d09d9d432bcef363bb05ad2942eb8bcc25caaf1` |
| `A_original/mesh2x2/demux_16.v` | `phase3/designs/mesh2x2_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `A_original/mesh2x2/dff_asynch_clr.v` | `phase3/designs/mesh2x2_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `A_original/mesh2x2/dff_synch_clr.v` | `phase3/designs/mesh2x2_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `A_original/mesh2x2/dff_synch_reset.v` | `phase3/designs/mesh2x2_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `A_original/mesh2x2/dff_synch_set.v` | `phase3/designs/mesh2x2_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `A_original/mesh2x2/encoder.v` | `phase3/designs/mesh2x2_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `A_original/mesh2x2/falling_edge_pulse_generator.v` | `phase3/designs/mesh2x2_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `A_original/mesh2x2/fop.v` | `phase3/designs/mesh2x2_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `A_original/mesh2x2/gray_mod6.v` | `phase3/designs/mesh2x2_ref/gray_mod6.v` | `573d5d4a73db10d594b32a6a179121868c330ec2b35de020081b6b8ca6c87002` |
| `A_original/mesh2x2/ip_chnl.v` | `phase3/designs/mesh2x2_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `A_original/mesh2x2/ip_link.v` | `phase3/designs/mesh2x2_ref/ip_link.v` | `274ed86db1b94f6da7f0b213d7cf89a839a67942506d351511d07b97f5f53501` |
| `A_original/mesh2x2/IRS.v` | `phase3/designs/mesh2x2_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `A_original/mesh2x2/jk_ff.v` | `phase3/designs/mesh2x2_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `A_original/mesh2x2/memory.v` | `phase3/designs/mesh2x2_ref/memory.v` | `7e2cedb766e1e73831dca04b00ffb88886b022d344ce44201dcee52fa020d6cc` |
| `A_original/mesh2x2/mesh_router2x2.v` | `phase3/designs/mesh2x2_ref/mesh_router2x2.v` | `8845909cdd62829c46cb60e3c8245911cc507cd96ab3c30aca34f942191f5c57` |
| `A_original/mesh2x2/mux.v` | `phase3/designs/mesh2x2_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `A_original/mesh2x2/op_core.v` | `phase3/designs/mesh2x2_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `A_original/mesh2x2/op_data_path.v` | `phase3/designs/mesh2x2_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `A_original/mesh2x2/op_link1.v` | `phase3/designs/mesh2x2_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `A_original/mesh2x2/op_link2.v` | `phase3/designs/mesh2x2_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `A_original/mesh2x2/op_link3.v` | `phase3/designs/mesh2x2_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `A_original/mesh2x2/op_link4.v` | `phase3/designs/mesh2x2_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `A_original/mesh2x2/priority_encoder.v` | `phase3/designs/mesh2x2_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `A_original/mesh2x2/register_1bit.v` | `phase3/designs/mesh2x2_ref/register_1bit.v` | `5d4b8564b7d1027245f2236a899c7c3e3846534000689b7b371df6e840d9198b` |
| `A_original/mesh2x2/register_32bit.v` | `phase3/designs/mesh2x2_ref/register_32bit.v` | `25918dc924e9af5628cbb09d70df8be153aeca5a170a4e7a5e920e8615470f4c` |
| `A_original/mesh2x2/register_4bit.v` | `phase3/designs/mesh2x2_ref/register_4bit.v` | `514bef71c2972956fdeade04b4823d140cf6f8261f21f5f8ab5308758350557e` |
| `A_original/mesh2x2/round_robin_req.v` | `phase3/designs/mesh2x2_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `A_original/mesh2x2/router_fifo.v` | `phase3/designs/mesh2x2_ref/router_fifo.v` | `0161b571a2eecf0fe0749887008d4ebfc4bd624cfd1af6e025acdb96a4fc1224` |
| `A_original/mesh2x2/routing_algo_mesh.v` | `phase3/designs/mesh2x2_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `A_original/mesh2x2/rr_arbiter.v` | `phase3/designs/mesh2x2_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `A_original/mesh2x2/rr_comb_new.v` | `phase3/designs/mesh2x2_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `A_original/mesh2x2/top_module.v` | `phase3/designs/mesh2x2_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `A_original/mesh3x3/allot_vc.v` | `phase3/designs/mesh3x3_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `A_original/mesh3x3/asynch_comparator.v` | `phase3/designs/mesh3x3_ref/asynch_comparator.v` | `3a2fefc860f8f880266edadd89a758609f94884462c1daddda8d371993e4a649` |
| `A_original/mesh3x3/demux_16.v` | `phase3/designs/mesh3x3_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `A_original/mesh3x3/dff_asynch_clr.v` | `phase3/designs/mesh3x3_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `A_original/mesh3x3/dff_synch_clr.v` | `phase3/designs/mesh3x3_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `A_original/mesh3x3/dff_synch_reset.v` | `phase3/designs/mesh3x3_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `A_original/mesh3x3/dff_synch_set.v` | `phase3/designs/mesh3x3_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `A_original/mesh3x3/encoder.v` | `phase3/designs/mesh3x3_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `A_original/mesh3x3/falling_edge_pulse_generator.v` | `phase3/designs/mesh3x3_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `A_original/mesh3x3/fop.v` | `phase3/designs/mesh3x3_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `A_original/mesh3x3/gray_mod6.v` | `phase3/designs/mesh3x3_ref/gray_mod6.v` | `20d7ec860b2dbee42d07ee79b22f9cefe57940e5a7c808728031f215c86b4165` |
| `A_original/mesh3x3/ip_chnl.v` | `phase3/designs/mesh3x3_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `A_original/mesh3x3/ip_link.v` | `phase3/designs/mesh3x3_ref/ip_link.v` | `abf70c12af7667913388266ea4b0743fc7c117f236855eff7b59805795d91914` |
| `A_original/mesh3x3/IRS.v` | `phase3/designs/mesh3x3_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `A_original/mesh3x3/jk_ff.v` | `phase3/designs/mesh3x3_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `A_original/mesh3x3/memory.v` | `phase3/designs/mesh3x3_ref/memory.v` | `7ee1357d16ebbdc27de1ff9af6aa38b9ce4e2f63d5775ae1858b50084dd9f9c7` |
| `A_original/mesh3x3/mesh_router3x3.v` | `phase3/designs/mesh3x3_ref/mesh_router3x3.v` | `dd19672dac96e7438a3495e90e94c4a00b5b73a153f7c9d5f2c994a00b2a37df` |
| `A_original/mesh3x3/mux.v` | `phase3/designs/mesh3x3_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `A_original/mesh3x3/op_core.v` | `phase3/designs/mesh3x3_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `A_original/mesh3x3/op_data_path.v` | `phase3/designs/mesh3x3_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `A_original/mesh3x3/op_link1.v` | `phase3/designs/mesh3x3_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `A_original/mesh3x3/op_link2.v` | `phase3/designs/mesh3x3_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `A_original/mesh3x3/op_link3.v` | `phase3/designs/mesh3x3_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `A_original/mesh3x3/op_link4.v` | `phase3/designs/mesh3x3_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `A_original/mesh3x3/priority_encoder.v` | `phase3/designs/mesh3x3_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `A_original/mesh3x3/register_1bit.v` | `phase3/designs/mesh3x3_ref/register_1bit.v` | `5d4b8564b7d1027245f2236a899c7c3e3846534000689b7b371df6e840d9198b` |
| `A_original/mesh3x3/register_32bit.v` | `phase3/designs/mesh3x3_ref/register_32bit.v` | `25918dc924e9af5628cbb09d70df8be153aeca5a170a4e7a5e920e8615470f4c` |
| `A_original/mesh3x3/register_4bit.v` | `phase3/designs/mesh3x3_ref/register_4bit.v` | `514bef71c2972956fdeade04b4823d140cf6f8261f21f5f8ab5308758350557e` |
| `A_original/mesh3x3/round_robin_req.v` | `phase3/designs/mesh3x3_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `A_original/mesh3x3/router_fifo.v` | `phase3/designs/mesh3x3_ref/router_fifo.v` | `aa139fa628650c6a8a65efeec1df5f01492d4b6b42fe335644171871c03cb425` |
| `A_original/mesh3x3/routing_algo_mesh.v` | `phase3/designs/mesh3x3_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `A_original/mesh3x3/rr_arbiter.v` | `phase3/designs/mesh3x3_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `A_original/mesh3x3/rr_comb_new.v` | `phase3/designs/mesh3x3_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `A_original/mesh3x3/top_module.v` | `phase3/designs/mesh3x3_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `A_original/mpsoc/adder.v` | `phase3/designs/mpsoc_ref/adder.v` | `f21e095778df9d4e649f16ccba75eec0703640cff2dd0eba914818b2ab98b1bb` |
| `A_original/mpsoc/address_fetch.v` | `phase3/designs/mpsoc_ref/address_fetch.v` | `c2954b3607895e48a9467be93f09c0c295f399b652ac133f9c01b2ba9e030fde` |
| `A_original/mpsoc/Address_select.v` | `phase3/designs/mpsoc_ref/Address_select.v` | `4dd66aba54acc0cd1fe3120d21182d7fb69ad08373c77e8b967d1113b87d8c40` |
| `A_original/mpsoc/allot_vc.v` | `phase3/designs/mpsoc_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `A_original/mpsoc/ALU.v` | `phase3/designs/mpsoc_ref/ALU.v` | `249a175643ba65cf816fd67c1e0de4dd2c1f0be54705e09c8cad2e6fac9edfef` |
| `A_original/mpsoc/asynch_comparator.v` | `phase3/designs/mpsoc_ref/asynch_comparator.v` | `b4557b38aed8ef3881524b9b7d09d9d432bcef363bb05ad2942eb8bcc25caaf1` |
| `A_original/mpsoc/Branch_Cal.v` | `phase3/designs/mpsoc_ref/Branch_Cal.v` | `b7907ae9eddcd35b474e75071c73b38d9930d8d5157d4f0d61c64a2f888c0453` |
| `A_original/mpsoc/Branch_comparator.v` | `phase3/designs/mpsoc_ref/Branch_comparator.v` | `866844561638a0de009c2ee44c059a5cbee4fe157161088e8b4191d1ff508b5f` |
| `A_original/mpsoc/control.v` | `phase3/designs/mpsoc_ref/control.v` | `3b639fc36a6a321dacc829569e34a4b9bee230d0564b94a361c6338ef7e6de1c` |
| `A_original/mpsoc/Data_mem.v` | `phase3/designs/mpsoc_ref/Data_mem.v` | `2ffdeb7e313461cd9f1400a13c98fa3365638016a4b98a9cbde426b43c390035` |
| `A_original/mpsoc/Decoder.v` | `phase3/designs/mpsoc_ref/Decoder.v` | `3afd37a82ce8b58eae162682214d979db57f82aae78b3b01ee8c65ef22dab8f8` |
| `A_original/mpsoc/demux_16.v` | `phase3/designs/mpsoc_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `A_original/mpsoc/depack.v` | `phase3/designs/mpsoc_ref/depack.v` | `06a8a1732cb9f57969f7226139d6b9437366c7095af917375a79edf8a57898ca` |
| `A_original/mpsoc/dff_asynch_clr.v` | `phase3/designs/mpsoc_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `A_original/mpsoc/dff_synch_clr.v` | `phase3/designs/mpsoc_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `A_original/mpsoc/dff_synch_reset.v` | `phase3/designs/mpsoc_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `A_original/mpsoc/dff_synch_set.v` | `phase3/designs/mpsoc_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `A_original/mpsoc/encoder.v` | `phase3/designs/mpsoc_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `A_original/mpsoc/ex_mem.v` | `phase3/designs/mpsoc_ref/ex_mem.v` | `fa69c8cd4a2da2f3714e62150b69f3395caae8dda91b3d2fffb12ed3839173bd` |
| `A_original/mpsoc/execute.v` | `phase3/designs/mpsoc_ref/execute.v` | `0eed9f7a017b6806cbc4a589c894b5986c59434de6311dc0f7ed5f0155f9503d` |
| `A_original/mpsoc/execution_unit.v` | `phase3/designs/mpsoc_ref/execution_unit.v` | `f43048e2060ec6e4fe254bc531a894d292d057c5baf771fb4d89ee28dc0806b5` |
| `A_original/mpsoc/falling_edge_pulse_generator.v` | `phase3/designs/mpsoc_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `A_original/mpsoc/fop.v` | `phase3/designs/mpsoc_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `A_original/mpsoc/forwarding_unit.v` | `phase3/designs/mpsoc_ref/forwarding_unit.v` | `a167a149221b77e78099e3dd0efce0f40605ac1532ab8f43b25ffd3945510c34` |
| `A_original/mpsoc/gray_mod6.v` | `phase3/designs/mpsoc_ref/gray_mod6.v` | `573d5d4a73db10d594b32a6a179121868c330ec2b35de020081b6b8ca6c87002` |
| `A_original/mpsoc/id_ex.v` | `phase3/designs/mpsoc_ref/id_ex.v` | `ff139e355ee8c5ee7a869c151f59e1f0049d6d5140a7c7d927d7c20d30a9fae8` |
| `A_original/mpsoc/if_id.v` | `phase3/designs/mpsoc_ref/if_id.v` | `710fda6c552b596adc9d065d37e8aceb9f7a8c1df193b9f1e1a395a212322398` |
| `A_original/mpsoc/IFU.v` | `phase3/designs/mpsoc_ref/IFU.v` | `1695f2216c8b00fa500c728506fc468fd19224de3e911327ffb709d79ce330e4` |
| `A_original/mpsoc/inst_mem.v` | `phase3/designs/mpsoc_ref/inst_mem.v` | `248fb494e7ed31bbfd6a45d029df047ed854bbc0c0e123331dd39ae933379c98` |
| `A_original/mpsoc/Inst_mem_integrated.v` | `phase3/designs/mpsoc_ref/Inst_mem_integrated.v` | `12ec8f623b331421693493ba9ebe5bd9bd7c60d42247bcee708db0693193c20a` |
| `A_original/mpsoc/ip_chnl.v` | `phase3/designs/mpsoc_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `A_original/mpsoc/ip_link.v` | `phase3/designs/mpsoc_ref/ip_link.v` | `274ed86db1b94f6da7f0b213d7cf89a839a67942506d351511d07b97f5f53501` |
| `A_original/mpsoc/IRS.v` | `phase3/designs/mpsoc_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `A_original/mpsoc/jk_ff.v` | `phase3/designs/mpsoc_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `A_original/mpsoc/main.v` | `phase3/designs/mpsoc_ref/main.v` | `6d613298e0ed1488fcd6a88ff3f40afd4aa4bd3c9cfc71c4381970af0806e934` |
| `A_original/mpsoc/mem_wb.v` | `phase3/designs/mpsoc_ref/mem_wb.v` | `73f5de75f101c7e79c5c00829f53b5ef007ea5ccc681c93163a8ccdfc5746062` |
| `A_original/mpsoc/mem_wb_mux.v` | `phase3/designs/mpsoc_ref/mem_wb_mux.v` | `43be6242ed1edd5c030e9ce498edf8f38bba73d657bd6c102ba414ed410880ee` |
| `A_original/mpsoc/memory.v` | `phase3/designs/mpsoc_ref/memory.v` | `7e2cedb766e1e73831dca04b00ffb88886b022d344ce44201dcee52fa020d6cc` |
| `A_original/mpsoc/mesh_router2x2.v` | `phase3/designs/mpsoc_ref/mesh_router2x2.v` | `8845909cdd62829c46cb60e3c8245911cc507cd96ab3c30aca34f942191f5c57` |
| `A_original/mpsoc/multiply.v` | `phase3/designs/mpsoc_ref/multiply.v` | `e8ad7ff2591e2c68eb4757b7865919f8d59df53d93edd8d7403d75f2e5a0e92c` |
| `A_original/mpsoc/mux.v` | `phase3/designs/mpsoc_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `A_original/mpsoc/mux3.v` | `phase3/designs/mpsoc_ref/mux3.v` | `f1d95d55993057a1efcf52f6eb3a15bbba75cce4eeb0fa75b28eb5db9dc49619` |
| `A_original/mpsoc/MuxPC.v` | `phase3/designs/mpsoc_ref/MuxPC.v` | `8e92ff841abe331db28145f337b61526c9680403a004b2faf3e676eb75f21f35` |
| `A_original/mpsoc/new.v` | `phase3/designs/mpsoc_ref/new.v` | `46951ab4b04254af6cf4ff23b4b28aa618c96f4e2719ccf32d66bb3a2c6b4ddd` |
| `A_original/mpsoc/new_mux.v` | `phase3/designs/mpsoc_ref/new_mux.v` | `c4f2de43161eae5b0494941f967901402a87bc2a528e7ad5deebcc444dc00e87` |
| `A_original/mpsoc/nidepack.v` | `phase3/designs/mpsoc_ref/nidepack.v` | `63efea876e75da22b067b545bbefacfb9120e5d1957b53d4e7414b37805a3688` |
| `A_original/mpsoc/op_core.v` | `phase3/designs/mpsoc_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `A_original/mpsoc/op_data_path.v` | `phase3/designs/mpsoc_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `A_original/mpsoc/op_link1.v` | `phase3/designs/mpsoc_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `A_original/mpsoc/op_link2.v` | `phase3/designs/mpsoc_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `A_original/mpsoc/op_link3.v` | `phase3/designs/mpsoc_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `A_original/mpsoc/op_link4.v` | `phase3/designs/mpsoc_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `A_original/mpsoc/priority_encoder.v` | `phase3/designs/mpsoc_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `A_original/mpsoc/Processor.v` | `phase3/designs/mpsoc_ref/Processor.v` | `f37cc5eac4075a9c5a28d0c972c2658b45518155370526ef398573de0fc8f00e` |
| `A_original/mpsoc/register_1bit.v` | `phase3/designs/mpsoc_ref/register_1bit.v` | `5d4b8564b7d1027245f2236a899c7c3e3846534000689b7b371df6e840d9198b` |
| `A_original/mpsoc/register_32bit.v` | `phase3/designs/mpsoc_ref/register_32bit.v` | `25918dc924e9af5628cbb09d70df8be153aeca5a170a4e7a5e920e8615470f4c` |
| `A_original/mpsoc/register_4bit.v` | `phase3/designs/mpsoc_ref/register_4bit.v` | `514bef71c2972956fdeade04b4823d140cf6f8261f21f5f8ab5308758350557e` |
| `A_original/mpsoc/round_robin_req.v` | `phase3/designs/mpsoc_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `A_original/mpsoc/router_fifo.v` | `phase3/designs/mpsoc_ref/router_fifo.v` | `0161b571a2eecf0fe0749887008d4ebfc4bd624cfd1af6e025acdb96a4fc1224` |
| `A_original/mpsoc/routing_algo_mesh.v` | `phase3/designs/mpsoc_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `A_original/mpsoc/rp1.v` | `phase3/designs/mpsoc_ref/rp1.v` | `4f89d6f88ad218b57f9b9540a8cfa86b744bbb9a26080447157b4c6323445871` |
| `A_original/mpsoc/rr_arbiter.v` | `phase3/designs/mpsoc_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `A_original/mpsoc/rr_comb_new.v` | `phase3/designs/mpsoc_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `A_original/mpsoc/stall_unit.v` | `phase3/designs/mpsoc_ref/stall_unit.v` | `b6b40729c82962de3d3d2f3cd61d78ceb0c55ed8d789c47feeb8b5893e78ae95` |
| `A_original/mpsoc/top_module.v` | `phase3/designs/mpsoc_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `B_repaired_golden/mesh2x2/__repaired_register_1bit.v` | `phase3/tasks/register_1bit/golden.v` | `6882d711c809e90728c66a9ecc6696bbdc81416f312522b6ad70f0e1c8aef4dd` |
| `B_repaired_golden/mesh2x2/__repaired_register_32bit.v` | `phase3/tasks/register_32bit/golden.v` | `8093f8f2fa0d7667fdc4f6bc02e3fa6be1d6c197996e4bb7a283bc6c61e78d60` |
| `B_repaired_golden/mesh2x2/__repaired_register_4bit.v` | `phase3/tasks/register_4bit/golden.v` | `d914413e52af6fa362b1647556cb0dcf0544dcfba63807a6a27bff727a4f6816` |
| `B_repaired_golden/mesh2x2/allot_vc.v` | `phase3/designs/mesh2x2_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `B_repaired_golden/mesh2x2/asynch_comparator.v` | `phase3/designs/mesh2x2_ref/asynch_comparator.v` | `b4557b38aed8ef3881524b9b7d09d9d432bcef363bb05ad2942eb8bcc25caaf1` |
| `B_repaired_golden/mesh2x2/demux_16.v` | `phase3/designs/mesh2x2_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `B_repaired_golden/mesh2x2/dff_asynch_clr.v` | `phase3/designs/mesh2x2_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `B_repaired_golden/mesh2x2/dff_synch_clr.v` | `phase3/designs/mesh2x2_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `B_repaired_golden/mesh2x2/dff_synch_reset.v` | `phase3/designs/mesh2x2_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `B_repaired_golden/mesh2x2/dff_synch_set.v` | `phase3/designs/mesh2x2_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `B_repaired_golden/mesh2x2/encoder.v` | `phase3/designs/mesh2x2_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `B_repaired_golden/mesh2x2/falling_edge_pulse_generator.v` | `phase3/designs/mesh2x2_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `B_repaired_golden/mesh2x2/fop.v` | `phase3/designs/mesh2x2_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `B_repaired_golden/mesh2x2/gray_mod6.v` | `phase3/designs/mesh2x2_ref/gray_mod6.v` | `573d5d4a73db10d594b32a6a179121868c330ec2b35de020081b6b8ca6c87002` |
| `B_repaired_golden/mesh2x2/ip_chnl.v` | `phase3/designs/mesh2x2_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `B_repaired_golden/mesh2x2/ip_link.v` | `phase3/designs/mesh2x2_ref/ip_link.v` | `274ed86db1b94f6da7f0b213d7cf89a839a67942506d351511d07b97f5f53501` |
| `B_repaired_golden/mesh2x2/IRS.v` | `phase3/designs/mesh2x2_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `B_repaired_golden/mesh2x2/jk_ff.v` | `phase3/designs/mesh2x2_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `B_repaired_golden/mesh2x2/memory.v` | `phase3/designs/mesh2x2_ref/memory.v` | `7e2cedb766e1e73831dca04b00ffb88886b022d344ce44201dcee52fa020d6cc` |
| `B_repaired_golden/mesh2x2/mesh_router2x2.v` | `phase3/designs/mesh2x2_ref/mesh_router2x2.v` | `8845909cdd62829c46cb60e3c8245911cc507cd96ab3c30aca34f942191f5c57` |
| `B_repaired_golden/mesh2x2/mux.v` | `phase3/designs/mesh2x2_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `B_repaired_golden/mesh2x2/op_core.v` | `phase3/designs/mesh2x2_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `B_repaired_golden/mesh2x2/op_data_path.v` | `phase3/designs/mesh2x2_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `B_repaired_golden/mesh2x2/op_link1.v` | `phase3/designs/mesh2x2_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `B_repaired_golden/mesh2x2/op_link2.v` | `phase3/designs/mesh2x2_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `B_repaired_golden/mesh2x2/op_link3.v` | `phase3/designs/mesh2x2_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `B_repaired_golden/mesh2x2/op_link4.v` | `phase3/designs/mesh2x2_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `B_repaired_golden/mesh2x2/priority_encoder.v` | `phase3/designs/mesh2x2_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `B_repaired_golden/mesh2x2/register_1bit.v` | `phase3/designs/mesh2x2_ref/register_1bit.v (compose.py stripped: register_1bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `B_repaired_golden/mesh2x2/register_32bit.v` | `phase3/designs/mesh2x2_ref/register_32bit.v (compose.py stripped: register_32bit)` | `25134e9690374aaed8764f402187309a342e09c50ea012e67dfae279f09eff26` |
| `B_repaired_golden/mesh2x2/register_4bit.v` | `phase3/designs/mesh2x2_ref/register_4bit.v (compose.py stripped: register_4bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `B_repaired_golden/mesh2x2/round_robin_req.v` | `phase3/designs/mesh2x2_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `B_repaired_golden/mesh2x2/router_fifo.v` | `phase3/designs/mesh2x2_ref/router_fifo.v` | `0161b571a2eecf0fe0749887008d4ebfc4bd624cfd1af6e025acdb96a4fc1224` |
| `B_repaired_golden/mesh2x2/routing_algo_mesh.v` | `phase3/designs/mesh2x2_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `B_repaired_golden/mesh2x2/rr_arbiter.v` | `phase3/designs/mesh2x2_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `B_repaired_golden/mesh2x2/rr_comb_new.v` | `phase3/designs/mesh2x2_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `B_repaired_golden/mesh2x2/top_module.v` | `phase3/designs/mesh2x2_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `B_repaired_golden/mesh3x3/__repaired_register_1bit.v` | `phase3/tasks/register_1bit/golden.v` | `6882d711c809e90728c66a9ecc6696bbdc81416f312522b6ad70f0e1c8aef4dd` |
| `B_repaired_golden/mesh3x3/__repaired_register_32bit.v` | `phase3/tasks/register_32bit/golden.v` | `8093f8f2fa0d7667fdc4f6bc02e3fa6be1d6c197996e4bb7a283bc6c61e78d60` |
| `B_repaired_golden/mesh3x3/__repaired_register_4bit.v` | `phase3/tasks/register_4bit/golden.v` | `d914413e52af6fa362b1647556cb0dcf0544dcfba63807a6a27bff727a4f6816` |
| `B_repaired_golden/mesh3x3/allot_vc.v` | `phase3/designs/mesh3x3_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `B_repaired_golden/mesh3x3/asynch_comparator.v` | `phase3/designs/mesh3x3_ref/asynch_comparator.v` | `3a2fefc860f8f880266edadd89a758609f94884462c1daddda8d371993e4a649` |
| `B_repaired_golden/mesh3x3/demux_16.v` | `phase3/designs/mesh3x3_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `B_repaired_golden/mesh3x3/dff_asynch_clr.v` | `phase3/designs/mesh3x3_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `B_repaired_golden/mesh3x3/dff_synch_clr.v` | `phase3/designs/mesh3x3_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `B_repaired_golden/mesh3x3/dff_synch_reset.v` | `phase3/designs/mesh3x3_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `B_repaired_golden/mesh3x3/dff_synch_set.v` | `phase3/designs/mesh3x3_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `B_repaired_golden/mesh3x3/encoder.v` | `phase3/designs/mesh3x3_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `B_repaired_golden/mesh3x3/falling_edge_pulse_generator.v` | `phase3/designs/mesh3x3_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `B_repaired_golden/mesh3x3/fop.v` | `phase3/designs/mesh3x3_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `B_repaired_golden/mesh3x3/gray_mod6.v` | `phase3/designs/mesh3x3_ref/gray_mod6.v` | `20d7ec860b2dbee42d07ee79b22f9cefe57940e5a7c808728031f215c86b4165` |
| `B_repaired_golden/mesh3x3/ip_chnl.v` | `phase3/designs/mesh3x3_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `B_repaired_golden/mesh3x3/ip_link.v` | `phase3/designs/mesh3x3_ref/ip_link.v` | `abf70c12af7667913388266ea4b0743fc7c117f236855eff7b59805795d91914` |
| `B_repaired_golden/mesh3x3/IRS.v` | `phase3/designs/mesh3x3_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `B_repaired_golden/mesh3x3/jk_ff.v` | `phase3/designs/mesh3x3_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `B_repaired_golden/mesh3x3/memory.v` | `phase3/designs/mesh3x3_ref/memory.v` | `7ee1357d16ebbdc27de1ff9af6aa38b9ce4e2f63d5775ae1858b50084dd9f9c7` |
| `B_repaired_golden/mesh3x3/mesh_router3x3.v` | `phase3/designs/mesh3x3_ref/mesh_router3x3.v` | `dd19672dac96e7438a3495e90e94c4a00b5b73a153f7c9d5f2c994a00b2a37df` |
| `B_repaired_golden/mesh3x3/mux.v` | `phase3/designs/mesh3x3_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `B_repaired_golden/mesh3x3/op_core.v` | `phase3/designs/mesh3x3_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `B_repaired_golden/mesh3x3/op_data_path.v` | `phase3/designs/mesh3x3_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `B_repaired_golden/mesh3x3/op_link1.v` | `phase3/designs/mesh3x3_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `B_repaired_golden/mesh3x3/op_link2.v` | `phase3/designs/mesh3x3_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `B_repaired_golden/mesh3x3/op_link3.v` | `phase3/designs/mesh3x3_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `B_repaired_golden/mesh3x3/op_link4.v` | `phase3/designs/mesh3x3_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `B_repaired_golden/mesh3x3/priority_encoder.v` | `phase3/designs/mesh3x3_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `B_repaired_golden/mesh3x3/register_1bit.v` | `phase3/designs/mesh3x3_ref/register_1bit.v (compose.py stripped: register_1bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `B_repaired_golden/mesh3x3/register_32bit.v` | `phase3/designs/mesh3x3_ref/register_32bit.v (compose.py stripped: register_32bit)` | `25134e9690374aaed8764f402187309a342e09c50ea012e67dfae279f09eff26` |
| `B_repaired_golden/mesh3x3/register_4bit.v` | `phase3/designs/mesh3x3_ref/register_4bit.v (compose.py stripped: register_4bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `B_repaired_golden/mesh3x3/round_robin_req.v` | `phase3/designs/mesh3x3_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `B_repaired_golden/mesh3x3/router_fifo.v` | `phase3/designs/mesh3x3_ref/router_fifo.v` | `aa139fa628650c6a8a65efeec1df5f01492d4b6b42fe335644171871c03cb425` |
| `B_repaired_golden/mesh3x3/routing_algo_mesh.v` | `phase3/designs/mesh3x3_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `B_repaired_golden/mesh3x3/rr_arbiter.v` | `phase3/designs/mesh3x3_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `B_repaired_golden/mesh3x3/rr_comb_new.v` | `phase3/designs/mesh3x3_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `B_repaired_golden/mesh3x3/top_module.v` | `phase3/designs/mesh3x3_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `B_repaired_golden/mpsoc/__repaired_Address_select.v` | `phase3/tasks/Address_select/golden.v` | `68fdf6e342f885d21263aaa18ddea5bb16781f953a47fbca2fcd3fcdc920ecb6` |
| `B_repaired_golden/mpsoc/__repaired_execute_mux.v` | `phase3/tasks/execute_mux/golden.v` | `f224ec00971598cdee767f9386c36122a523bec05b83309adeceecc9c2aa51bc` |
| `B_repaired_golden/mpsoc/__repaired_mem_wb_mux.v` | `phase3/tasks/mem_wb_mux/golden.v` | `9ebe55ed2da3c07ac993745e3cb8e022ed900b3e52eb93d39d325e778fb761bd` |
| `B_repaired_golden/mpsoc/__repaired_mux3.v` | `phase3/tasks/mux3/golden.v` | `67529711c5058570bae878264459dc52af289dfefd82377d82fa3132d52373ac` |
| `B_repaired_golden/mpsoc/__repaired_MuxPC.v` | `phase3/tasks/MuxPC/golden.v` | `ad63d7da16ddfdf7ed184b47fa56f212be0a12518e80219a9121bc6f5e5bccf6` |
| `B_repaired_golden/mpsoc/__repaired_register_1bit.v` | `phase3/tasks/register_1bit/golden.v` | `6882d711c809e90728c66a9ecc6696bbdc81416f312522b6ad70f0e1c8aef4dd` |
| `B_repaired_golden/mpsoc/__repaired_register_32bit.v` | `phase3/tasks/register_32bit/golden.v` | `8093f8f2fa0d7667fdc4f6bc02e3fa6be1d6c197996e4bb7a283bc6c61e78d60` |
| `B_repaired_golden/mpsoc/__repaired_register_4bit.v` | `phase3/tasks/register_4bit/golden.v` | `d914413e52af6fa362b1647556cb0dcf0544dcfba63807a6a27bff727a4f6816` |
| `B_repaired_golden/mpsoc/adder.v` | `phase3/designs/mpsoc_ref/adder.v` | `f21e095778df9d4e649f16ccba75eec0703640cff2dd0eba914818b2ab98b1bb` |
| `B_repaired_golden/mpsoc/address_fetch.v` | `phase3/designs/mpsoc_ref/address_fetch.v` | `c2954b3607895e48a9467be93f09c0c295f399b652ac133f9c01b2ba9e030fde` |
| `B_repaired_golden/mpsoc/Address_select.v` | `phase3/designs/mpsoc_ref/Address_select.v (compose.py stripped: Address_select)` | `4dee67f565d9bd6c0bc25c48cc604abc246e8b2af7a2e94991bb3d5ecc0b055f` |
| `B_repaired_golden/mpsoc/allot_vc.v` | `phase3/designs/mpsoc_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `B_repaired_golden/mpsoc/ALU.v` | `phase3/designs/mpsoc_ref/ALU.v` | `249a175643ba65cf816fd67c1e0de4dd2c1f0be54705e09c8cad2e6fac9edfef` |
| `B_repaired_golden/mpsoc/asynch_comparator.v` | `phase3/designs/mpsoc_ref/asynch_comparator.v` | `b4557b38aed8ef3881524b9b7d09d9d432bcef363bb05ad2942eb8bcc25caaf1` |
| `B_repaired_golden/mpsoc/Branch_Cal.v` | `phase3/designs/mpsoc_ref/Branch_Cal.v` | `b7907ae9eddcd35b474e75071c73b38d9930d8d5157d4f0d61c64a2f888c0453` |
| `B_repaired_golden/mpsoc/Branch_comparator.v` | `phase3/designs/mpsoc_ref/Branch_comparator.v` | `866844561638a0de009c2ee44c059a5cbee4fe157161088e8b4191d1ff508b5f` |
| `B_repaired_golden/mpsoc/control.v` | `phase3/designs/mpsoc_ref/control.v` | `3b639fc36a6a321dacc829569e34a4b9bee230d0564b94a361c6338ef7e6de1c` |
| `B_repaired_golden/mpsoc/Data_mem.v` | `phase3/designs/mpsoc_ref/Data_mem.v` | `2ffdeb7e313461cd9f1400a13c98fa3365638016a4b98a9cbde426b43c390035` |
| `B_repaired_golden/mpsoc/Decoder.v` | `phase3/designs/mpsoc_ref/Decoder.v` | `3afd37a82ce8b58eae162682214d979db57f82aae78b3b01ee8c65ef22dab8f8` |
| `B_repaired_golden/mpsoc/demux_16.v` | `phase3/designs/mpsoc_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `B_repaired_golden/mpsoc/depack.v` | `phase3/designs/mpsoc_ref/depack.v` | `06a8a1732cb9f57969f7226139d6b9437366c7095af917375a79edf8a57898ca` |
| `B_repaired_golden/mpsoc/dff_asynch_clr.v` | `phase3/designs/mpsoc_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `B_repaired_golden/mpsoc/dff_synch_clr.v` | `phase3/designs/mpsoc_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `B_repaired_golden/mpsoc/dff_synch_reset.v` | `phase3/designs/mpsoc_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `B_repaired_golden/mpsoc/dff_synch_set.v` | `phase3/designs/mpsoc_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `B_repaired_golden/mpsoc/encoder.v` | `phase3/designs/mpsoc_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `B_repaired_golden/mpsoc/ex_mem.v` | `phase3/designs/mpsoc_ref/ex_mem.v` | `fa69c8cd4a2da2f3714e62150b69f3395caae8dda91b3d2fffb12ed3839173bd` |
| `B_repaired_golden/mpsoc/execute.v` | `phase3/designs/mpsoc_ref/execute.v` | `0eed9f7a017b6806cbc4a589c894b5986c59434de6311dc0f7ed5f0155f9503d` |
| `B_repaired_golden/mpsoc/execution_unit.v` | `phase3/designs/mpsoc_ref/execution_unit.v (compose.py stripped: execute_mux)` | `b526094799e00cc5c402f8c68f46154e30b52b5dd506bf0fb31c327b64b38ecb` |
| `B_repaired_golden/mpsoc/falling_edge_pulse_generator.v` | `phase3/designs/mpsoc_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `B_repaired_golden/mpsoc/fop.v` | `phase3/designs/mpsoc_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `B_repaired_golden/mpsoc/forwarding_unit.v` | `phase3/designs/mpsoc_ref/forwarding_unit.v` | `a167a149221b77e78099e3dd0efce0f40605ac1532ab8f43b25ffd3945510c34` |
| `B_repaired_golden/mpsoc/gray_mod6.v` | `phase3/designs/mpsoc_ref/gray_mod6.v` | `573d5d4a73db10d594b32a6a179121868c330ec2b35de020081b6b8ca6c87002` |
| `B_repaired_golden/mpsoc/id_ex.v` | `phase3/designs/mpsoc_ref/id_ex.v` | `ff139e355ee8c5ee7a869c151f59e1f0049d6d5140a7c7d927d7c20d30a9fae8` |
| `B_repaired_golden/mpsoc/if_id.v` | `phase3/designs/mpsoc_ref/if_id.v` | `710fda6c552b596adc9d065d37e8aceb9f7a8c1df193b9f1e1a395a212322398` |
| `B_repaired_golden/mpsoc/IFU.v` | `phase3/designs/mpsoc_ref/IFU.v` | `1695f2216c8b00fa500c728506fc468fd19224de3e911327ffb709d79ce330e4` |
| `B_repaired_golden/mpsoc/inst_mem.v` | `phase3/designs/mpsoc_ref/inst_mem.v` | `248fb494e7ed31bbfd6a45d029df047ed854bbc0c0e123331dd39ae933379c98` |
| `B_repaired_golden/mpsoc/Inst_mem_integrated.v` | `phase3/designs/mpsoc_ref/Inst_mem_integrated.v` | `12ec8f623b331421693493ba9ebe5bd9bd7c60d42247bcee708db0693193c20a` |
| `B_repaired_golden/mpsoc/ip_chnl.v` | `phase3/designs/mpsoc_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `B_repaired_golden/mpsoc/ip_link.v` | `phase3/designs/mpsoc_ref/ip_link.v` | `274ed86db1b94f6da7f0b213d7cf89a839a67942506d351511d07b97f5f53501` |
| `B_repaired_golden/mpsoc/IRS.v` | `phase3/designs/mpsoc_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `B_repaired_golden/mpsoc/jk_ff.v` | `phase3/designs/mpsoc_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `B_repaired_golden/mpsoc/main.v` | `phase3/designs/mpsoc_ref/main.v` | `6d613298e0ed1488fcd6a88ff3f40afd4aa4bd3c9cfc71c4381970af0806e934` |
| `B_repaired_golden/mpsoc/mem_wb.v` | `phase3/designs/mpsoc_ref/mem_wb.v` | `73f5de75f101c7e79c5c00829f53b5ef007ea5ccc681c93163a8ccdfc5746062` |
| `B_repaired_golden/mpsoc/mem_wb_mux.v` | `phase3/designs/mpsoc_ref/mem_wb_mux.v (compose.py stripped: mem_wb_mux)` | `4dee67f565d9bd6c0bc25c48cc604abc246e8b2af7a2e94991bb3d5ecc0b055f` |
| `B_repaired_golden/mpsoc/memory.v` | `phase3/designs/mpsoc_ref/memory.v` | `7e2cedb766e1e73831dca04b00ffb88886b022d344ce44201dcee52fa020d6cc` |
| `B_repaired_golden/mpsoc/mesh_router2x2.v` | `phase3/designs/mpsoc_ref/mesh_router2x2.v` | `8845909cdd62829c46cb60e3c8245911cc507cd96ab3c30aca34f942191f5c57` |
| `B_repaired_golden/mpsoc/multiply.v` | `phase3/designs/mpsoc_ref/multiply.v` | `e8ad7ff2591e2c68eb4757b7865919f8d59df53d93edd8d7403d75f2e5a0e92c` |
| `B_repaired_golden/mpsoc/mux.v` | `phase3/designs/mpsoc_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `B_repaired_golden/mpsoc/mux3.v` | `phase3/designs/mpsoc_ref/mux3.v (compose.py stripped: mux3)` | `543f1486eed69cbd6c8d31487f8db01d708469d726e1aef512def27b8d51e497` |
| `B_repaired_golden/mpsoc/MuxPC.v` | `phase3/designs/mpsoc_ref/MuxPC.v (compose.py stripped: MuxPC)` | `4dee67f565d9bd6c0bc25c48cc604abc246e8b2af7a2e94991bb3d5ecc0b055f` |
| `B_repaired_golden/mpsoc/new.v` | `phase3/designs/mpsoc_ref/new.v` | `46951ab4b04254af6cf4ff23b4b28aa618c96f4e2719ccf32d66bb3a2c6b4ddd` |
| `B_repaired_golden/mpsoc/new_mux.v` | `phase3/designs/mpsoc_ref/new_mux.v` | `c4f2de43161eae5b0494941f967901402a87bc2a528e7ad5deebcc444dc00e87` |
| `B_repaired_golden/mpsoc/nidepack.v` | `phase3/designs/mpsoc_ref/nidepack.v` | `63efea876e75da22b067b545bbefacfb9120e5d1957b53d4e7414b37805a3688` |
| `B_repaired_golden/mpsoc/op_core.v` | `phase3/designs/mpsoc_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `B_repaired_golden/mpsoc/op_data_path.v` | `phase3/designs/mpsoc_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `B_repaired_golden/mpsoc/op_link1.v` | `phase3/designs/mpsoc_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `B_repaired_golden/mpsoc/op_link2.v` | `phase3/designs/mpsoc_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `B_repaired_golden/mpsoc/op_link3.v` | `phase3/designs/mpsoc_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `B_repaired_golden/mpsoc/op_link4.v` | `phase3/designs/mpsoc_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `B_repaired_golden/mpsoc/priority_encoder.v` | `phase3/designs/mpsoc_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `B_repaired_golden/mpsoc/Processor.v` | `phase3/designs/mpsoc_ref/Processor.v` | `f37cc5eac4075a9c5a28d0c972c2658b45518155370526ef398573de0fc8f00e` |
| `B_repaired_golden/mpsoc/register_1bit.v` | `phase3/designs/mpsoc_ref/register_1bit.v (compose.py stripped: register_1bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `B_repaired_golden/mpsoc/register_32bit.v` | `phase3/designs/mpsoc_ref/register_32bit.v (compose.py stripped: register_32bit)` | `25134e9690374aaed8764f402187309a342e09c50ea012e67dfae279f09eff26` |
| `B_repaired_golden/mpsoc/register_4bit.v` | `phase3/designs/mpsoc_ref/register_4bit.v (compose.py stripped: register_4bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `B_repaired_golden/mpsoc/round_robin_req.v` | `phase3/designs/mpsoc_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `B_repaired_golden/mpsoc/router_fifo.v` | `phase3/designs/mpsoc_ref/router_fifo.v` | `0161b571a2eecf0fe0749887008d4ebfc4bd624cfd1af6e025acdb96a4fc1224` |
| `B_repaired_golden/mpsoc/routing_algo_mesh.v` | `phase3/designs/mpsoc_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `B_repaired_golden/mpsoc/rp1.v` | `phase3/designs/mpsoc_ref/rp1.v` | `4f89d6f88ad218b57f9b9540a8cfa86b744bbb9a26080447157b4c6323445871` |
| `B_repaired_golden/mpsoc/rr_arbiter.v` | `phase3/designs/mpsoc_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `B_repaired_golden/mpsoc/rr_comb_new.v` | `phase3/designs/mpsoc_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `B_repaired_golden/mpsoc/stall_unit.v` | `phase3/designs/mpsoc_ref/stall_unit.v` | `b6b40729c82962de3d3d2f3cd61d78ceb0c55ed8d789c47feeb8b5893e78ae95` |
| `B_repaired_golden/mpsoc/top_module.v` | `phase3/designs/mpsoc_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `C_repaired_stitch/mesh2x2/__repaired_register_1bit.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_1bit/rep2/iter3/dut.v` | `12d8d563ed9643432986383ebaea6e09a512ffeeaeb59b1ea11365cec0246ba1` |
| `C_repaired_stitch/mesh2x2/__repaired_register_32bit.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_32bit/rep2/iter2/dut.v` | `aad7a6171b0ed7cefdafa8c69092c31b0f07f420e7379e8e7d7eeb77c46ea7a9` |
| `C_repaired_stitch/mesh2x2/__repaired_register_4bit.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_4bit/rep2/iter2/dut.v` | `81b4324801afefa67cada60147fc1c02dd99ad09b1f0f836c8162d4d7458aefc` |
| `C_repaired_stitch/mesh2x2/allot_vc.v` | `phase3/designs/mesh2x2_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `C_repaired_stitch/mesh2x2/asynch_comparator.v` | `phase3/designs/mesh2x2_ref/asynch_comparator.v` | `b4557b38aed8ef3881524b9b7d09d9d432bcef363bb05ad2942eb8bcc25caaf1` |
| `C_repaired_stitch/mesh2x2/demux_16.v` | `phase3/designs/mesh2x2_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `C_repaired_stitch/mesh2x2/dff_asynch_clr.v` | `phase3/designs/mesh2x2_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `C_repaired_stitch/mesh2x2/dff_synch_clr.v` | `phase3/designs/mesh2x2_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `C_repaired_stitch/mesh2x2/dff_synch_reset.v` | `phase3/designs/mesh2x2_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `C_repaired_stitch/mesh2x2/dff_synch_set.v` | `phase3/designs/mesh2x2_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `C_repaired_stitch/mesh2x2/encoder.v` | `phase3/designs/mesh2x2_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `C_repaired_stitch/mesh2x2/falling_edge_pulse_generator.v` | `phase3/designs/mesh2x2_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `C_repaired_stitch/mesh2x2/fop.v` | `phase3/designs/mesh2x2_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `C_repaired_stitch/mesh2x2/gray_mod6.v` | `phase3/designs/mesh2x2_ref/gray_mod6.v` | `573d5d4a73db10d594b32a6a179121868c330ec2b35de020081b6b8ca6c87002` |
| `C_repaired_stitch/mesh2x2/ip_chnl.v` | `phase3/designs/mesh2x2_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `C_repaired_stitch/mesh2x2/ip_link.v` | `phase3/designs/mesh2x2_ref/ip_link.v` | `274ed86db1b94f6da7f0b213d7cf89a839a67942506d351511d07b97f5f53501` |
| `C_repaired_stitch/mesh2x2/IRS.v` | `phase3/designs/mesh2x2_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `C_repaired_stitch/mesh2x2/jk_ff.v` | `phase3/designs/mesh2x2_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `C_repaired_stitch/mesh2x2/memory.v` | `phase3/designs/mesh2x2_ref/memory.v` | `7e2cedb766e1e73831dca04b00ffb88886b022d344ce44201dcee52fa020d6cc` |
| `C_repaired_stitch/mesh2x2/mesh_router2x2.v` | `phase3/designs/mesh2x2_ref/mesh_router2x2.v` | `8845909cdd62829c46cb60e3c8245911cc507cd96ab3c30aca34f942191f5c57` |
| `C_repaired_stitch/mesh2x2/mux.v` | `phase3/designs/mesh2x2_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `C_repaired_stitch/mesh2x2/op_core.v` | `phase3/designs/mesh2x2_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `C_repaired_stitch/mesh2x2/op_data_path.v` | `phase3/designs/mesh2x2_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `C_repaired_stitch/mesh2x2/op_link1.v` | `phase3/designs/mesh2x2_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `C_repaired_stitch/mesh2x2/op_link2.v` | `phase3/designs/mesh2x2_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `C_repaired_stitch/mesh2x2/op_link3.v` | `phase3/designs/mesh2x2_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `C_repaired_stitch/mesh2x2/op_link4.v` | `phase3/designs/mesh2x2_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `C_repaired_stitch/mesh2x2/priority_encoder.v` | `phase3/designs/mesh2x2_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `C_repaired_stitch/mesh2x2/register_1bit.v` | `phase3/designs/mesh2x2_ref/register_1bit.v (compose.py stripped: register_1bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `C_repaired_stitch/mesh2x2/register_32bit.v` | `phase3/designs/mesh2x2_ref/register_32bit.v (compose.py stripped: register_32bit)` | `25134e9690374aaed8764f402187309a342e09c50ea012e67dfae279f09eff26` |
| `C_repaired_stitch/mesh2x2/register_4bit.v` | `phase3/designs/mesh2x2_ref/register_4bit.v (compose.py stripped: register_4bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `C_repaired_stitch/mesh2x2/round_robin_req.v` | `phase3/designs/mesh2x2_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `C_repaired_stitch/mesh2x2/router_fifo.v` | `phase3/designs/mesh2x2_ref/router_fifo.v` | `0161b571a2eecf0fe0749887008d4ebfc4bd624cfd1af6e025acdb96a4fc1224` |
| `C_repaired_stitch/mesh2x2/routing_algo_mesh.v` | `phase3/designs/mesh2x2_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `C_repaired_stitch/mesh2x2/rr_arbiter.v` | `phase3/designs/mesh2x2_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `C_repaired_stitch/mesh2x2/rr_comb_new.v` | `phase3/designs/mesh2x2_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `C_repaired_stitch/mesh2x2/top_module.v` | `phase3/designs/mesh2x2_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `C_repaired_stitch/mesh3x3/__repaired_register_1bit.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_1bit/rep2/iter3/dut.v` | `12d8d563ed9643432986383ebaea6e09a512ffeeaeb59b1ea11365cec0246ba1` |
| `C_repaired_stitch/mesh3x3/__repaired_register_32bit.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_32bit/rep2/iter2/dut.v` | `aad7a6171b0ed7cefdafa8c69092c31b0f07f420e7379e8e7d7eeb77c46ea7a9` |
| `C_repaired_stitch/mesh3x3/__repaired_register_4bit.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_4bit/rep2/iter2/dut.v` | `81b4324801afefa67cada60147fc1c02dd99ad09b1f0f836c8162d4d7458aefc` |
| `C_repaired_stitch/mesh3x3/allot_vc.v` | `phase3/designs/mesh3x3_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `C_repaired_stitch/mesh3x3/asynch_comparator.v` | `phase3/designs/mesh3x3_ref/asynch_comparator.v` | `3a2fefc860f8f880266edadd89a758609f94884462c1daddda8d371993e4a649` |
| `C_repaired_stitch/mesh3x3/demux_16.v` | `phase3/designs/mesh3x3_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `C_repaired_stitch/mesh3x3/dff_asynch_clr.v` | `phase3/designs/mesh3x3_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `C_repaired_stitch/mesh3x3/dff_synch_clr.v` | `phase3/designs/mesh3x3_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `C_repaired_stitch/mesh3x3/dff_synch_reset.v` | `phase3/designs/mesh3x3_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `C_repaired_stitch/mesh3x3/dff_synch_set.v` | `phase3/designs/mesh3x3_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `C_repaired_stitch/mesh3x3/encoder.v` | `phase3/designs/mesh3x3_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `C_repaired_stitch/mesh3x3/falling_edge_pulse_generator.v` | `phase3/designs/mesh3x3_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `C_repaired_stitch/mesh3x3/fop.v` | `phase3/designs/mesh3x3_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `C_repaired_stitch/mesh3x3/gray_mod6.v` | `phase3/designs/mesh3x3_ref/gray_mod6.v` | `20d7ec860b2dbee42d07ee79b22f9cefe57940e5a7c808728031f215c86b4165` |
| `C_repaired_stitch/mesh3x3/ip_chnl.v` | `phase3/designs/mesh3x3_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `C_repaired_stitch/mesh3x3/ip_link.v` | `phase3/designs/mesh3x3_ref/ip_link.v` | `abf70c12af7667913388266ea4b0743fc7c117f236855eff7b59805795d91914` |
| `C_repaired_stitch/mesh3x3/IRS.v` | `phase3/designs/mesh3x3_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `C_repaired_stitch/mesh3x3/jk_ff.v` | `phase3/designs/mesh3x3_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `C_repaired_stitch/mesh3x3/memory.v` | `phase3/designs/mesh3x3_ref/memory.v` | `7ee1357d16ebbdc27de1ff9af6aa38b9ce4e2f63d5775ae1858b50084dd9f9c7` |
| `C_repaired_stitch/mesh3x3/mesh_router3x3.v` | `phase3/designs/mesh3x3_ref/mesh_router3x3.v` | `dd19672dac96e7438a3495e90e94c4a00b5b73a153f7c9d5f2c994a00b2a37df` |
| `C_repaired_stitch/mesh3x3/mux.v` | `phase3/designs/mesh3x3_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `C_repaired_stitch/mesh3x3/op_core.v` | `phase3/designs/mesh3x3_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `C_repaired_stitch/mesh3x3/op_data_path.v` | `phase3/designs/mesh3x3_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `C_repaired_stitch/mesh3x3/op_link1.v` | `phase3/designs/mesh3x3_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `C_repaired_stitch/mesh3x3/op_link2.v` | `phase3/designs/mesh3x3_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `C_repaired_stitch/mesh3x3/op_link3.v` | `phase3/designs/mesh3x3_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `C_repaired_stitch/mesh3x3/op_link4.v` | `phase3/designs/mesh3x3_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `C_repaired_stitch/mesh3x3/priority_encoder.v` | `phase3/designs/mesh3x3_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `C_repaired_stitch/mesh3x3/register_1bit.v` | `phase3/designs/mesh3x3_ref/register_1bit.v (compose.py stripped: register_1bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `C_repaired_stitch/mesh3x3/register_32bit.v` | `phase3/designs/mesh3x3_ref/register_32bit.v (compose.py stripped: register_32bit)` | `25134e9690374aaed8764f402187309a342e09c50ea012e67dfae279f09eff26` |
| `C_repaired_stitch/mesh3x3/register_4bit.v` | `phase3/designs/mesh3x3_ref/register_4bit.v (compose.py stripped: register_4bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `C_repaired_stitch/mesh3x3/round_robin_req.v` | `phase3/designs/mesh3x3_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `C_repaired_stitch/mesh3x3/router_fifo.v` | `phase3/designs/mesh3x3_ref/router_fifo.v` | `aa139fa628650c6a8a65efeec1df5f01492d4b6b42fe335644171871c03cb425` |
| `C_repaired_stitch/mesh3x3/routing_algo_mesh.v` | `phase3/designs/mesh3x3_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `C_repaired_stitch/mesh3x3/rr_arbiter.v` | `phase3/designs/mesh3x3_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `C_repaired_stitch/mesh3x3/rr_comb_new.v` | `phase3/designs/mesh3x3_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `C_repaired_stitch/mesh3x3/top_module.v` | `phase3/designs/mesh3x3_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `C_repaired_stitch/mpsoc/__repaired_Address_select.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/Address_select/rep2/iter3/dut.v` | `dc58d5a211236397b7949867cf6c11f9863d25a8a5b251fe56536d9ea20948be` |
| `C_repaired_stitch/mpsoc/__repaired_execute_mux.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/execute_mux/rep2/iter2/dut.v` | `a6a7a3c5e967cc120193c87515b9a227c1e08d19be62bfd3ce57801dd2e67b15` |
| `C_repaired_stitch/mpsoc/__repaired_mem_wb_mux.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/mem_wb_mux/rep2/iter6/dut.v` | `b455657c6779d91db0f4012b56ddccd1ddc5dce32759b0101981849cd09423d4` |
| `C_repaired_stitch/mpsoc/__repaired_mux3.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/mux3/rep2/iter1/dut.v` | `86f02eccef957ab55e7167547b00c99e0361df039c9440ad9a3a47f0856cfc51` |
| `C_repaired_stitch/mpsoc/__repaired_MuxPC.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/MuxPC/rep2/iter3/dut.v` | `ce9417b5db6095f85a3c1b9a0e68e30711ad63e7b1384eca4b6c1a0b2aa1c2c7` |
| `C_repaired_stitch/mpsoc/__repaired_register_1bit.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_1bit/rep2/iter3/dut.v` | `12d8d563ed9643432986383ebaea6e09a512ffeeaeb59b1ea11365cec0246ba1` |
| `C_repaired_stitch/mpsoc/__repaired_register_32bit.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_32bit/rep2/iter2/dut.v` | `aad7a6171b0ed7cefdafa8c69092c31b0f07f420e7379e8e7d7eeb77c46ea7a9` |
| `C_repaired_stitch/mpsoc/__repaired_register_4bit.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_4bit/rep2/iter2/dut.v` | `81b4324801afefa67cada60147fc1c02dd99ad09b1f0f836c8162d4d7458aefc` |
| `C_repaired_stitch/mpsoc/adder.v` | `phase3/designs/mpsoc_ref/adder.v` | `f21e095778df9d4e649f16ccba75eec0703640cff2dd0eba914818b2ab98b1bb` |
| `C_repaired_stitch/mpsoc/address_fetch.v` | `phase3/designs/mpsoc_ref/address_fetch.v` | `c2954b3607895e48a9467be93f09c0c295f399b652ac133f9c01b2ba9e030fde` |
| `C_repaired_stitch/mpsoc/Address_select.v` | `phase3/designs/mpsoc_ref/Address_select.v (compose.py stripped: Address_select)` | `4dee67f565d9bd6c0bc25c48cc604abc246e8b2af7a2e94991bb3d5ecc0b055f` |
| `C_repaired_stitch/mpsoc/allot_vc.v` | `phase3/designs/mpsoc_ref/allot_vc.v` | `87425f1e459d8a8e93911de986281dc7eb1b5c7fb77b78a53c61e1ce5179bca2` |
| `C_repaired_stitch/mpsoc/ALU.v` | `phase3/designs/mpsoc_ref/ALU.v` | `249a175643ba65cf816fd67c1e0de4dd2c1f0be54705e09c8cad2e6fac9edfef` |
| `C_repaired_stitch/mpsoc/asynch_comparator.v` | `phase3/designs/mpsoc_ref/asynch_comparator.v` | `b4557b38aed8ef3881524b9b7d09d9d432bcef363bb05ad2942eb8bcc25caaf1` |
| `C_repaired_stitch/mpsoc/Branch_Cal.v` | `phase3/designs/mpsoc_ref/Branch_Cal.v` | `b7907ae9eddcd35b474e75071c73b38d9930d8d5157d4f0d61c64a2f888c0453` |
| `C_repaired_stitch/mpsoc/Branch_comparator.v` | `phase3/designs/mpsoc_ref/Branch_comparator.v` | `866844561638a0de009c2ee44c059a5cbee4fe157161088e8b4191d1ff508b5f` |
| `C_repaired_stitch/mpsoc/control.v` | `phase3/designs/mpsoc_ref/control.v` | `3b639fc36a6a321dacc829569e34a4b9bee230d0564b94a361c6338ef7e6de1c` |
| `C_repaired_stitch/mpsoc/Data_mem.v` | `phase3/designs/mpsoc_ref/Data_mem.v` | `2ffdeb7e313461cd9f1400a13c98fa3365638016a4b98a9cbde426b43c390035` |
| `C_repaired_stitch/mpsoc/Decoder.v` | `phase3/designs/mpsoc_ref/Decoder.v` | `3afd37a82ce8b58eae162682214d979db57f82aae78b3b01ee8c65ef22dab8f8` |
| `C_repaired_stitch/mpsoc/demux_16.v` | `phase3/designs/mpsoc_ref/demux_16.v` | `6a566a991a0b16d3f06124f9b112f5167a9c0a8dfa04417cb83046cb2b8796e1` |
| `C_repaired_stitch/mpsoc/depack.v` | `phase3/designs/mpsoc_ref/depack.v` | `06a8a1732cb9f57969f7226139d6b9437366c7095af917375a79edf8a57898ca` |
| `C_repaired_stitch/mpsoc/dff_asynch_clr.v` | `phase3/designs/mpsoc_ref/dff_asynch_clr.v` | `eb2859b11efdabd25adf83ff85cd1c68cc7fec353426b207cd78dd19d871005e` |
| `C_repaired_stitch/mpsoc/dff_synch_clr.v` | `phase3/designs/mpsoc_ref/dff_synch_clr.v` | `594b5f8e077e4d3e1fa0e91198662b8649754250df7a9f220c900ff6434b6dd4` |
| `C_repaired_stitch/mpsoc/dff_synch_reset.v` | `phase3/designs/mpsoc_ref/dff_synch_reset.v` | `c85cf10a0ede3d0e79283cf7a566fbbe813427597979609e6ebf4ae537677e6a` |
| `C_repaired_stitch/mpsoc/dff_synch_set.v` | `phase3/designs/mpsoc_ref/dff_synch_set.v` | `c087d00e7fdf2d7381d87a2f0f2921c079f58d87168892f0b3d02eb7ab3c9072` |
| `C_repaired_stitch/mpsoc/encoder.v` | `phase3/designs/mpsoc_ref/encoder.v` | `86d85fcd26a2691ff41ce277cf696bbd6811004514034a6888449f3c3f435a49` |
| `C_repaired_stitch/mpsoc/ex_mem.v` | `phase3/designs/mpsoc_ref/ex_mem.v` | `fa69c8cd4a2da2f3714e62150b69f3395caae8dda91b3d2fffb12ed3839173bd` |
| `C_repaired_stitch/mpsoc/execute.v` | `phase3/designs/mpsoc_ref/execute.v` | `0eed9f7a017b6806cbc4a589c894b5986c59434de6311dc0f7ed5f0155f9503d` |
| `C_repaired_stitch/mpsoc/execution_unit.v` | `phase3/designs/mpsoc_ref/execution_unit.v (compose.py stripped: execute_mux)` | `b526094799e00cc5c402f8c68f46154e30b52b5dd506bf0fb31c327b64b38ecb` |
| `C_repaired_stitch/mpsoc/falling_edge_pulse_generator.v` | `phase3/designs/mpsoc_ref/falling_edge_pulse_generator.v` | `2ecd238beb95601f5a575535e7bd4ed6ce9015e6ad9d7f1650f5ee9dd60a6320` |
| `C_repaired_stitch/mpsoc/fop.v` | `phase3/designs/mpsoc_ref/fop.v` | `d0a8a9412397cb7a4a7ce46581935f1aeeea3cafba6bd1fedf39074511a182c0` |
| `C_repaired_stitch/mpsoc/forwarding_unit.v` | `phase3/designs/mpsoc_ref/forwarding_unit.v` | `a167a149221b77e78099e3dd0efce0f40605ac1532ab8f43b25ffd3945510c34` |
| `C_repaired_stitch/mpsoc/gray_mod6.v` | `phase3/designs/mpsoc_ref/gray_mod6.v` | `573d5d4a73db10d594b32a6a179121868c330ec2b35de020081b6b8ca6c87002` |
| `C_repaired_stitch/mpsoc/id_ex.v` | `phase3/designs/mpsoc_ref/id_ex.v` | `ff139e355ee8c5ee7a869c151f59e1f0049d6d5140a7c7d927d7c20d30a9fae8` |
| `C_repaired_stitch/mpsoc/if_id.v` | `phase3/designs/mpsoc_ref/if_id.v` | `710fda6c552b596adc9d065d37e8aceb9f7a8c1df193b9f1e1a395a212322398` |
| `C_repaired_stitch/mpsoc/IFU.v` | `phase3/designs/mpsoc_ref/IFU.v` | `1695f2216c8b00fa500c728506fc468fd19224de3e911327ffb709d79ce330e4` |
| `C_repaired_stitch/mpsoc/inst_mem.v` | `phase3/designs/mpsoc_ref/inst_mem.v` | `248fb494e7ed31bbfd6a45d029df047ed854bbc0c0e123331dd39ae933379c98` |
| `C_repaired_stitch/mpsoc/Inst_mem_integrated.v` | `phase3/designs/mpsoc_ref/Inst_mem_integrated.v` | `12ec8f623b331421693493ba9ebe5bd9bd7c60d42247bcee708db0693193c20a` |
| `C_repaired_stitch/mpsoc/ip_chnl.v` | `phase3/designs/mpsoc_ref/ip_chnl.v` | `1bb73c45a08a49384bb186050cf70790c4671740b917d9b496e65eb3a11b85df` |
| `C_repaired_stitch/mpsoc/ip_link.v` | `phase3/designs/mpsoc_ref/ip_link.v` | `274ed86db1b94f6da7f0b213d7cf89a839a67942506d351511d07b97f5f53501` |
| `C_repaired_stitch/mpsoc/IRS.v` | `phase3/designs/mpsoc_ref/IRS.v` | `336845c14afcaacc19beb8ea6ca238c1d5464c437e87b35af6add063f6bf8b73` |
| `C_repaired_stitch/mpsoc/jk_ff.v` | `phase3/designs/mpsoc_ref/jk_ff.v` | `48b73e3c5446f34479ec4df707ea847b7a16cb993ef8a4d1e31fe93a4db3b3d2` |
| `C_repaired_stitch/mpsoc/main.v` | `phase3/designs/mpsoc_ref/main.v` | `6d613298e0ed1488fcd6a88ff3f40afd4aa4bd3c9cfc71c4381970af0806e934` |
| `C_repaired_stitch/mpsoc/mem_wb.v` | `phase3/designs/mpsoc_ref/mem_wb.v` | `73f5de75f101c7e79c5c00829f53b5ef007ea5ccc681c93163a8ccdfc5746062` |
| `C_repaired_stitch/mpsoc/mem_wb_mux.v` | `phase3/designs/mpsoc_ref/mem_wb_mux.v (compose.py stripped: mem_wb_mux)` | `4dee67f565d9bd6c0bc25c48cc604abc246e8b2af7a2e94991bb3d5ecc0b055f` |
| `C_repaired_stitch/mpsoc/memory.v` | `phase3/designs/mpsoc_ref/memory.v` | `7e2cedb766e1e73831dca04b00ffb88886b022d344ce44201dcee52fa020d6cc` |
| `C_repaired_stitch/mpsoc/mesh_router2x2.v` | `phase3/designs/mpsoc_ref/mesh_router2x2.v` | `8845909cdd62829c46cb60e3c8245911cc507cd96ab3c30aca34f942191f5c57` |
| `C_repaired_stitch/mpsoc/multiply.v` | `phase3/designs/mpsoc_ref/multiply.v` | `e8ad7ff2591e2c68eb4757b7865919f8d59df53d93edd8d7403d75f2e5a0e92c` |
| `C_repaired_stitch/mpsoc/mux.v` | `phase3/designs/mpsoc_ref/mux.v` | `8ff302cff244c901a65e644b20c5adc9b4d889dcfea061dd7653adc2346548b2` |
| `C_repaired_stitch/mpsoc/mux3.v` | `phase3/designs/mpsoc_ref/mux3.v (compose.py stripped: mux3)` | `543f1486eed69cbd6c8d31487f8db01d708469d726e1aef512def27b8d51e497` |
| `C_repaired_stitch/mpsoc/MuxPC.v` | `phase3/designs/mpsoc_ref/MuxPC.v (compose.py stripped: MuxPC)` | `4dee67f565d9bd6c0bc25c48cc604abc246e8b2af7a2e94991bb3d5ecc0b055f` |
| `C_repaired_stitch/mpsoc/new.v` | `phase3/designs/mpsoc_ref/new.v` | `46951ab4b04254af6cf4ff23b4b28aa618c96f4e2719ccf32d66bb3a2c6b4ddd` |
| `C_repaired_stitch/mpsoc/new_mux.v` | `phase3/designs/mpsoc_ref/new_mux.v` | `c4f2de43161eae5b0494941f967901402a87bc2a528e7ad5deebcc444dc00e87` |
| `C_repaired_stitch/mpsoc/nidepack.v` | `phase3/designs/mpsoc_ref/nidepack.v` | `63efea876e75da22b067b545bbefacfb9120e5d1957b53d4e7414b37805a3688` |
| `C_repaired_stitch/mpsoc/op_core.v` | `phase3/designs/mpsoc_ref/op_core.v` | `4c843a3d23eb2430d9a029c0d6d503852c052ce3c961fad734738912af963e1a` |
| `C_repaired_stitch/mpsoc/op_data_path.v` | `phase3/designs/mpsoc_ref/op_data_path.v` | `2a5e65a7ed2d39f9ca96b80798fff58c39b5629a4a11d3779a9bc4f55281f5af` |
| `C_repaired_stitch/mpsoc/op_link1.v` | `phase3/designs/mpsoc_ref/op_link1.v` | `dfa10e5e4fe747abb96f2696773a98a4f5f30948be35e5b3b8f626f6e3f150c0` |
| `C_repaired_stitch/mpsoc/op_link2.v` | `phase3/designs/mpsoc_ref/op_link2.v` | `7602dfdfff76f54f80625d1a2df0b1d93f0eb41d80c2cb6b8e5272abb83986c2` |
| `C_repaired_stitch/mpsoc/op_link3.v` | `phase3/designs/mpsoc_ref/op_link3.v` | `d9d8955b64e5bc91df303fc73cf88e8dbf5c659151950f9071b84fcddebd9a2d` |
| `C_repaired_stitch/mpsoc/op_link4.v` | `phase3/designs/mpsoc_ref/op_link4.v` | `ae5d19849a998e4f882b3ab0bb68bdef0400bc8959fe013d0efca9ab929f65a0` |
| `C_repaired_stitch/mpsoc/priority_encoder.v` | `phase3/designs/mpsoc_ref/priority_encoder.v` | `607713b8356a683f485e761ca7e0daabd096d959b0eb9fc4e90e81eff44e9394` |
| `C_repaired_stitch/mpsoc/Processor.v` | `phase3/designs/mpsoc_ref/Processor.v` | `f37cc5eac4075a9c5a28d0c972c2658b45518155370526ef398573de0fc8f00e` |
| `C_repaired_stitch/mpsoc/register_1bit.v` | `phase3/designs/mpsoc_ref/register_1bit.v (compose.py stripped: register_1bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `C_repaired_stitch/mpsoc/register_32bit.v` | `phase3/designs/mpsoc_ref/register_32bit.v (compose.py stripped: register_32bit)` | `25134e9690374aaed8764f402187309a342e09c50ea012e67dfae279f09eff26` |
| `C_repaired_stitch/mpsoc/register_4bit.v` | `phase3/designs/mpsoc_ref/register_4bit.v (compose.py stripped: register_4bit)` | `e0f36872a39b8075bf51c58c42fe5d9099b8ebf9406e09ab65c88f2e78e9817d` |
| `C_repaired_stitch/mpsoc/round_robin_req.v` | `phase3/designs/mpsoc_ref/round_robin_req.v` | `a1875de3ef426866fa8f2db147324d40ccbf0fc13060d1385f77f9aff952f6bb` |
| `C_repaired_stitch/mpsoc/router_fifo.v` | `phase3/designs/mpsoc_ref/router_fifo.v` | `0161b571a2eecf0fe0749887008d4ebfc4bd624cfd1af6e025acdb96a4fc1224` |
| `C_repaired_stitch/mpsoc/routing_algo_mesh.v` | `phase3/designs/mpsoc_ref/routing_algo_mesh.v` | `0d99bf49e30d71de8b80b582507350e154b1bba36577bf5a09c790d9429842cc` |
| `C_repaired_stitch/mpsoc/rp1.v` | `phase3/designs/mpsoc_ref/rp1.v` | `4f89d6f88ad218b57f9b9540a8cfa86b744bbb9a26080447157b4c6323445871` |
| `C_repaired_stitch/mpsoc/rr_arbiter.v` | `phase3/designs/mpsoc_ref/rr_arbiter.v` | `0f4368f5eabde3817fcc00b5ee0f41743907a3181d4bbac6e77b4b453804fdcd` |
| `C_repaired_stitch/mpsoc/rr_comb_new.v` | `phase3/designs/mpsoc_ref/rr_comb_new.v` | `45bf1b0933d51f9d6314a9bd209d6c8efe7b670ccc3f09855c2f837bd5c8adb5` |
| `C_repaired_stitch/mpsoc/stall_unit.v` | `phase3/designs/mpsoc_ref/stall_unit.v` | `b6b40729c82962de3d3d2f3cd61d78ceb0c55ed8d789c47feeb8b5893e78ae95` |
| `C_repaired_stitch/mpsoc/top_module.v` | `phase3/designs/mpsoc_ref/top_module.v` | `50676eb017b9890d32d1bfef47a89d836f8c74df11bb0fd589425aad5d25649e` |
| `COWORKER_BRIEF.md` | `user-provided exact brief` | `fe7be947759903b5ecef27ed903d6df5ac2ba32f7839e5f9d186de48fcbaa2e4` |
| `leaves/Address_select/defective.v` | `phase3/tasks/Address_select/input.v` | `6bb92a03038ccfb1307704f247ac327e170609a1ff4c3f1046b8879143dec138` |
| `leaves/Address_select/golden.v` | `phase3/tasks/Address_select/golden.v` | `68fdf6e342f885d21263aaa18ddea5bb16781f953a47fbca2fcd3fcdc920ecb6` |
| `leaves/Address_select/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/Address_select/rep2/iter3/dut.v` | `dc58d5a211236397b7949867cf6c11f9863d25a8a5b251fe56536d9ea20948be` |
| `leaves/execute_mux/defective.v` | `phase3/tasks/execute_mux/input.v` | `fcda9b34eb3d2c6465ce71a6fafb53e6f3948c1921b126f663d4336b8f5e03c1` |
| `leaves/execute_mux/golden.v` | `phase3/tasks/execute_mux/golden.v` | `f224ec00971598cdee767f9386c36122a523bec05b83309adeceecc9c2aa51bc` |
| `leaves/execute_mux/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/execute_mux/rep2/iter2/dut.v` | `a6a7a3c5e967cc120193c87515b9a227c1e08d19be62bfd3ce57801dd2e67b15` |
| `leaves/mem_wb_mux/defective.v` | `phase3/tasks/mem_wb_mux/input.v` | `49f3aa2cec9b6e51fd46aef45ec7a9abc8c6e5ef83aff9a6917727f78d5dccb5` |
| `leaves/mem_wb_mux/golden.v` | `phase3/tasks/mem_wb_mux/golden.v` | `9ebe55ed2da3c07ac993745e3cb8e022ed900b3e52eb93d39d325e778fb761bd` |
| `leaves/mem_wb_mux/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/mem_wb_mux/rep2/iter6/dut.v` | `b455657c6779d91db0f4012b56ddccd1ddc5dce32759b0101981849cd09423d4` |
| `leaves/mux3/defective.v` | `phase3/tasks/mux3/input.v` | `a886f6f0d72dad9c7f0edc3921767ea06f4a5125e94ba21b6e959180d1b2ed6c` |
| `leaves/mux3/golden.v` | `phase3/tasks/mux3/golden.v` | `67529711c5058570bae878264459dc52af289dfefd82377d82fa3132d52373ac` |
| `leaves/mux3/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/mux3/rep2/iter1/dut.v` | `86f02eccef957ab55e7167547b00c99e0361df039c9440ad9a3a47f0856cfc51` |
| `leaves/MuxPC/defective.v` | `phase3/tasks/MuxPC/input.v` | `d6c4ce3aec133d603ca9f4b0bcd37ef1285ca459022fd1da67c3d852332fd590` |
| `leaves/MuxPC/golden.v` | `phase3/tasks/MuxPC/golden.v` | `ad63d7da16ddfdf7ed184b47fa56f212be0a12518e80219a9121bc6f5e5bccf6` |
| `leaves/MuxPC/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/MuxPC/rep2/iter3/dut.v` | `ce9417b5db6095f85a3c1b9a0e68e30711ad63e7b1384eca4b6c1a0b2aa1c2c7` |
| `leaves/ni_flit_pack/defective.v` | `phase3/tasks/ni_flit_pack/input.v` | `f9babc5b5d03711040d2dfb11cc2eb37a613f8cd42a136b597ec48468da38afe` |
| `leaves/ni_flit_pack/golden.v` | `phase3/tasks/ni_flit_pack/golden.v` | `7f0909c2f711e0d0eecabc36fb21fdfe8f033d3ca222505322071946c0a9fb62` |
| `leaves/ni_flit_pack/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/ni_flit_pack/rep2/iter1/dut.v` | `76f0c6e4beaef46270b62f0d9e0cf8fbc4a46affbaf4018ea3e0a05475458ebe` |
| `leaves/noc_xbar4/defective.v` | `phase3/tasks/noc_xbar4/input.v` | `784e6b8ba6e0597eb5fd3741d87b7cf0ee24ed739bb6ea297bf49c13b7ec5dd9` |
| `leaves/noc_xbar4/golden.v` | `phase3/tasks/noc_xbar4/golden.v` | `db39caca09543638f0eeaaa5e31572dc6e34d6cc01f289ec58201d0b55b6357b` |
| `leaves/noc_xbar4/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/noc_xbar4/rep2/iter6/dut.v` | `b607d661418b7107ccaeb60cff562f802d157063c7168aa7e6e41022d90bdc58` |
| `leaves/register_1bit/defective.v` | `phase3/tasks/register_1bit/input.v` | `81cf8c18e57e3109e6efa099391ec6153b9d6bec7f1f3f907bf288808c0dba84` |
| `leaves/register_1bit/golden.v` | `phase3/tasks/register_1bit/golden.v` | `6882d711c809e90728c66a9ecc6696bbdc81416f312522b6ad70f0e1c8aef4dd` |
| `leaves/register_1bit/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_1bit/rep2/iter3/dut.v` | `12d8d563ed9643432986383ebaea6e09a512ffeeaeb59b1ea11365cec0246ba1` |
| `leaves/register_32bit/defective.v` | `phase3/tasks/register_32bit/input.v` | `606b0300815bf407fc4b57ae7ce36e273310c0d7b315c23dfaeabf89339779bf` |
| `leaves/register_32bit/golden.v` | `phase3/tasks/register_32bit/golden.v` | `8093f8f2fa0d7667fdc4f6bc02e3fa6be1d6c197996e4bb7a283bc6c61e78d60` |
| `leaves/register_32bit/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_32bit/rep2/iter2/dut.v` | `aad7a6171b0ed7cefdafa8c69092c31b0f07f420e7379e8e7d7eeb77c46ea7a9` |
| `leaves/register_4bit/defective.v` | `phase3/tasks/register_4bit/input.v` | `5010979a0b5cdc6ee46f6ab930887cbf74737a7cd88555b527e19c87ce6667ec` |
| `leaves/register_4bit/golden.v` | `phase3/tasks/register_4bit/golden.v` | `d914413e52af6fa362b1647556cb0dcf0544dcfba63807a6a27bff727a4f6816` |
| `leaves/register_4bit/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_4bit/rep2/iter2/dut.v` | `81b4324801afefa67cada60147fc1c02dd99ad09b1f0f836c8162d4d7458aefc` |
| `leaves/riscv_alu_flags/defective.v` | `phase3/tasks/riscv_alu_flags/input.v` | `45f479c9d117e2aa0344e0e8c1d0ab3e111069131061f34c2df79fa55add9226` |
| `leaves/riscv_alu_flags/golden.v` | `phase3/tasks/riscv_alu_flags/golden.v` | `82842090af1e34e5f8eff0575dcdd95e6c0ee693dc201a04908a75f107016df8` |
| `leaves/riscv_alu_flags/stitch_repaired.v` | `phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/riscv_alu_flags/rep2/iter6/dut.v` | `e2bfd2331505dece38aea0fe1d7b8a9228f017156f6d27f887910d63a0afaf3e` |
| `PPA_SUMMARY.md` | `authored from the local OpenSTA/ORFS analysis bundle` | `26e634ca66597a74e136646661fe2ae13cf52881989555b7052d48dd9771f8ad` |
| `scripts/build_manifest.py` | `authored for this handoff` | `df492affdc11599e92aea4ed314261f40caf67ab0ad240cd00f453211cacd013` |
| `scripts/run_yosys_stat.sh` | `authored for this handoff` | `f1a2aaec107e128b5b77c86da21c82129f47bfad084d677a0432af901a448da1` |
