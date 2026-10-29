#!/usr/bin/env python3
"""Write a board's KiCad project file and the library tables.  Design rules are tighter than JLCPCB's
(0.127 mm track and gap, 0.3 mm via drill) so a board that passes DRC here passes there; the RF
board adds a net class for its 50 ohm lines.

    python3 scripts/gen_project.py amod_p
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts
from sexp import uid

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(HERE, "..", "hardware")
ROOT_SHEET_UUID = uid("sheet/root")

TRACK_MIN, CLEARANCE, VIA_DIA, VIA_DRILL = 0.2, 0.2, 0.6, 0.3


def net_class(name, track, clearance=CLEARANCE, priority=2147483647, via=VIA_DIA, drill=VIA_DRILL):
    return {"name": name, "clearance": clearance, "track_width": track, "via_diameter": via, "via_drill": drill,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
            "wire_width": 6, "bus_width": 12, "priority": priority}


FINE_RULES = dict(clearance=0.127, track=0.127, via=0.45, annular=0.10, drill=0.20, hole_clearance=0.25)    # the floor beside a 0.5 mm pitch QFN
FINE = {s: FINE_RULES for s, b in parts.BOARDS.items() if b.get("fine")}


def design_rules(stem=None):
    f = FINE.get(stem, {})
    return {"max_error": 0.005, "min_clearance": f.get("clearance", CLEARANCE), "min_connection": f.get("track", TRACK_MIN), "min_copper_edge_clearance": 0.3,
            "min_groove_width": 0.0, "min_hole_clearance": f.get("hole_clearance", 0.3), "min_hole_to_hole": 0.5, "min_microvia_diameter": 0.2,
            "min_microvia_drill": 0.1, "min_resolved_spokes": 2, "min_silk_clearance": 0.15, "min_text_height": 0.8,
            "min_text_thickness": 0.15, "min_through_hole_diameter": f.get("drill", 0.3), "min_track_width": f.get("track", TRACK_MIN),
            "min_via_annular_width": f.get("annular", 0.15), "min_via_diameter": f.get("via", VIA_DIA), "solder_mask_clearance": 0.0,
            "solder_mask_min_width": 0.0, "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True}


def severities():
    err = ["copper_edge_clearance", "copper_sliver", "courtyards_overlap", "drill_out_of_range", "duplicate_footprints", "footprint",
           "footprint_symbol_mismatch", "hole_clearance", "hole_near_hole", "invalid_outline", "isolated_copper", "item_on_disabled_layer",
           "lib_footprint_issues", "lib_footprint_mismatch", "malformed_courtyard", "microvia_drill_out_of_range", "missing_courtyard",
           "missing_footprint", "npth_inside_courtyard", "padstack", "pth_inside_courtyard", "shorting_items", "silk_over_copper",
           "silk_overlap", "solder_mask_bridge", "starved_thermal", "text_height", "text_thickness", "through_hole_pad_without_hole",
           "too_many_vias", "track_dangling", "track_width", "unconnected_items", "via_dangling", "zones_intersect"]
    warn = ["assertion_failure", "diff_pair_gap_out_of_range", "diff_pair_uncoupled_length_too_long", "footprint_filters_mismatch",
            "footprint_type_mismatch", "length_out_of_range", "mirrored_text_on_front_layer", "nonmirrored_text_on_back_layer",
            "skew_out_of_range", "track_angle", "track_segment_length", "connection_width"]
    out = {k: "error" for k in err}
    out.update({k: "warning" for k in warn})
    out["silk_over_copper"] = "warning"
    out["footprint_filters_mismatch"] = "ignore"
    out["lib_footprint_mismatch"] = "ignore"        # footprints get their fields and silk edited by the generator
    return out


def project(stem, layers, power_nets, rf_nets=(), fine_nets=(), fine_refs=()):
    # beside a fine-pitch chip the rails and ground meet its nets at the fine clearance (a Default net still gets 0.2)
    classes = [net_class("Default", 0.25), net_class("Power", 0.4, priority=1, clearance=(0.127 if fine_nets else CLEARANCE))]
    assignments = {n: ["Power"] for n in power_nets}
    if rf_nets:
        classes.append(net_class("RF", 0.29, clearance=0.25, priority=0))
        assignments.update({n: ["RF"] for n in rf_nets})
    if fine_nets:
        classes.append(net_class("Fine", 0.15, clearance=0.127, priority=0, via=0.45, drill=0.25))
        assignments.update({n: ["Fine"] for n in fine_nets if n not in assignments})
    return {
        "board": {"3dviewports": [], "design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5, "copper_text_size_v": 1.5,
                         "copper_text_thickness": 0.3, "courtyard_line_width": 0.05, "dimension_precision": 4, "dimension_units": 3,
                         "fab_line_width": 0.1, "fab_text_size_h": 1.0, "fab_text_size_v": 1.0, "fab_text_thickness": 0.15,
                         "other_line_width": 0.15, "other_text_size_h": 1.0, "other_text_size_v": 1.0, "other_text_thickness": 0.15,
                         "silk_line_width": 0.15, "silk_text_size_h": 1.0, "silk_text_size_v": 1.0, "silk_text_thickness": 0.15,
                         "zones": {"min_clearance": 0.3}},
            "diff_pair_dimensions": [], "drc_exclusions": [], "rule_severities": severities(), "rules": design_rules(stem),
            "track_widths": [0.0, 0.25, 0.35, 0.6], "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": VIA_DIA, "drill": VIA_DRILL}, {"diameter": 0.8, "drill": 0.4}],
            "zones_allow_external_fillets": False}, "layer_presets": [], "viewports": []},
        "boards": [], "cvpcb": {"equivalence_files": []},
        "erc": {"erc_exclusions": [], "meta": {"version": 0}, "pin_map": [], "rule_severities": {
            "bus_definition_conflict": "error", "bus_entry_needed": "error", "bus_to_bus_conflict": "error", "bus_to_net_conflict": "error",
            "conflicting_netclasses": "error", "different_unit_footprint": "error", "different_unit_net": "error", "duplicate_reference": "error",
            "duplicate_sheet_names": "error", "endpoint_off_grid": "error", "extra_units": "error", "footprint_link_issues": "error",
            "global_label_dangling": "warning", "hier_label_mismatch": "error", "label_dangling": "error", "lib_symbol_issues": "error",
            "missing_bidi_pin": "warning", "missing_input_pin": "warning", "missing_power_pin": "error", "missing_unit": "warning",
            "multiple_net_names": "warning", "net_not_bus_member": "warning", "no_connect_connected": "error", "no_connect_dangling": "warning",
            "pin_not_connected": "error", "pin_not_driven": "error", "pin_to_pin": "error", "power_pin_not_driven": "error",
            "similar_label_and_power": "warning", "similar_labels": "warning", "simulation_model_issue": "ignore", "single_global_label": "ignore",
            "unannotated": "error", "unconnected_wire_endpoint": "error", "unresolved_variable": "error", "wire_dangling": "error"}},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": stem + ".kicad_pro", "version": 3},
        "net_settings": {"classes": classes, "meta": {"version": 4}, "net_colors": None, "netclass_assignments": assignments,
                         "netclass_patterns": [{"netclass": "Fine", "pattern": "unconnected-(%s-*" % r} for r in fine_refs]},
        "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "", "pos_files": "", "specctra_dsn": "", "step": "", "svg": "", "vrml": ""},
                   "page_layout_descr_file": ""},
        "schematic": {"annotate_start_num": 0, "bom_fmt_presets": [], "bom_fmt_settings": {}, "bom_presets": [], "bom_settings": {},
                      "connection_grid_size": 50.0,
                      "drawing": {"dashed_lines_dash_length_ratio": 12.0, "dashed_lines_gap_length_ratio": 3.0, "default_line_thickness": 6.0,
                                  "default_text_size": 50.0, "field_names": [], "intersheets_ref_own_page": False, "intersheets_ref_prefix": "",
                                  "intersheets_ref_short": False, "intersheets_ref_show": False, "intersheets_ref_suffix": "", "junction_size_choice": 3,
                                  "label_size_ratio": 0.375, "operating_point_overlay_i_precision": 3, "operating_point_overlay_i_range": "~A",
                                  "operating_point_overlay_v_precision": 3, "operating_point_overlay_v_range": "~V", "overbar_offset_ratio": 1.23,
                                  "pin_symbol_size": 25.0, "text_offset_ratio": 0.15},
                      "legacy_lib_dir": "", "legacy_lib_list": [], "meta": {"version": 1}, "net_format_name": "", "page_layout_descr_file": "",
                      "plot_directory": "../out/", "space_save_all_events": True, "spice_current_sheet_as_root": False,
                      "spice_external_command": 'spice "%I"', "spice_model_current_sheet_as_root": True, "spice_save_all_currents": False,
                      "spice_save_all_dissipations": False, "spice_save_all_voltages": False, "subpart_first_id": 65, "subpart_id_separator": 0},
        "sheets": [[ROOT_SHEET_UUID, "Root"]], "text_variables": {}}


SYM_LIB_TABLE = '(sym_lib_table\n  (version 7)\n  (lib (name "amod")(type "KiCad")(uri "${KIPRJMOD}/lib/amod.kicad_sym")(options "")(descr "the project symbols"))\n)\n'
FP_LIB_TABLE = ('(fp_lib_table\n  (version 7)\n  (lib (name "amod")(type "KiCad")(uri "${KIPRJMOD}/lib/amod.pretty")(options "")'
                '(descr "Footprints drawn for the AMOD boards"))\n)\n')

POWER_NETS = {s: b["power_nets"] for s, b in parts.BOARDS.items()}


def main():
    stem = sys.argv[1] if len(sys.argv) > 1 else "amod_p"
    os.makedirs(HW, exist_ok=True)
    B = parts.BOARDS[stem]
    path = os.path.join(HW, stem + ".kicad_pro")
    # the RF net class: every net a tile draws as a 50 ohm line (tiles.RF_W), once the schematic stage has written the tiles
    rf_nets, fine_nets, fine_refs = [], [], []
    tj = os.path.join(HW, "..", "out", stem + "_tiles.json")
    if os.path.exists(tj):
        for t in json.load(open(tj))["tiles"]:
            for w in t["wires"]:
                if abs(w[2] - 0.29) < 1e-6 and w[0] not in rf_nets:
                    rf_nets.append(w[0])
            if t.get("fine"):                      # a fine-pitch tile: every net of its parts but the rails and ground
                for p in t["parts"]:
                    fine_refs.append(p["ref"])             # and its chips' unconnected pins, which sit 0.15 mm from their neighbours
                    for n in p["pins"].values():
                        if n not in POWER_NETS[stem] and n not in fine_nets:
                            fine_nets.append(n)
    with open(path, "w") as fh:
        json.dump(project(stem, B["layers"], POWER_NETS[stem], rf_nets, fine_nets, fine_refs), fh, indent=2)
        fh.write("\n")
    for name, body in (("sym-lib-table", SYM_LIB_TABLE), ("fp-lib-table", FP_LIB_TABLE)):
        with open(os.path.join(HW, name), "w") as fh:
            fh.write(body)
    print("  wrote %s and the library tables" % os.path.relpath(path))


if __name__ == "__main__":
    main()
