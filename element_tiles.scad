// Element tile generator (Korean-friendly)
// Usage from command line:
// openscad -o out/Te.stl -D "symbol='Te'" -D "name='텔루륨'" -D "number='127.60'" -D "atomic_number='52'" element_tiles.scad

symbol = "Te";
name = "텔루륨";
number = "127.60";
atomic_number = "52";

// Choose output piece
show_tile = true;
show_connector = false;

// Use an installed Nanum font. Change if your system uses a different family name.
font_name = "NanumGothic:style=Regular";

// ======================
// Main parameters
// ======================
tile_size = 80;
corner_radius = 5;
base_thickness = 4;

frame_width = 1.8;
frame_height = 0.6;

text_height = 0.6;
symbol_size = 25;
name_size = 7;
number_size = 7;
atomic_size = 7;

// Extra outline thickening applied around every glyph (mm).
// 0 keeps the font's native stroke; small positive values fatten strokes
// for better print legibility / "extra bold" feel.
text_thicken = 0;

slot_width = 25;
slot_height = 2.0;
slot_depth = 3.0;
slot_z = 1.2;

fit_clearance = 0.15;
connector_length = slot_width - 0.2;
connector_height = slot_height - fit_clearance;
connector_depth = 2*(slot_depth - fit_clearance);
connector_gap = 8;
connector_corner = 0.6;

atomic_x = -28;
atomic_y = 28;

symbol_x = 0;
symbol_y = 9;

name_x = 0;
name_y = -16;

number_x = 0;
number_y = -28;

module rounded_square(sz, r) {
    offset(r = r)
        square([sz - 2*r, sz - 2*r], center = true);
}

module outer_shape_2d() {
    rounded_square(tile_size, corner_radius);
}

frame_inset = 0.25;

module outer_frame_2d() {
    difference() {
        offset(delta = -frame_inset)
            outer_shape_2d();
        offset(delta = -(frame_inset + frame_width))
            outer_shape_2d();
    }
}

module base_body() {
    linear_extrude(height = base_thickness)
        outer_shape_2d();
}

module top_outer_frame() {
    translate([0,0,base_thickness])
        linear_extrude(height = frame_height)
            outer_frame_2d();
}

module left_slot() {
    translate([-tile_size/2 - 0.1, -slot_width/2, slot_z])
        cube([slot_depth + 0.2, slot_width, slot_height]);
}

module right_slot() {
    translate([tile_size/2 - slot_depth + 0.1, -slot_width/2, slot_z])
        cube([slot_depth + 0.2, slot_width, slot_height]);
}

module engraved_text(s, sz) {
    offset(r = text_thicken)
        text(s, size = sz, halign = "center", valign = "center", font = font_name);
}

module texts() {
    translate([atomic_x, atomic_y, base_thickness])
        linear_extrude(height = text_height)
            engraved_text(atomic_number, atomic_size);

    translate([symbol_x, symbol_y, base_thickness])
        linear_extrude(height = text_height)
            engraved_text(symbol, symbol_size);

    translate([name_x, name_y, base_thickness])
        linear_extrude(height = text_height)
            engraved_text(name, name_size);

    translate([number_x, number_y, base_thickness])
        linear_extrude(height = text_height)
            engraved_text(number, number_size);
}

module tile() {
    difference() {
        union() {
            base_body();
            top_outer_frame();
            texts();
        }
        left_slot();
        right_slot();
    }
}

module connector() {
    linear_extrude(height = connector_height)
        offset(r = connector_corner)
            square(
                [connector_depth - 2*connector_corner,
                 connector_length - 2*connector_corner],
                center = true
            );
}

if (show_tile)
    tile();

if (show_connector)
    translate([0, -(tile_size/2 + connector_gap), 0])
        rotate([0,0,90])
            connector();
