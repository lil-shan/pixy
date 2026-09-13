// Pixy — desktop console enclosure
//
// A wedge cabinet: the LED panel leans back ~10 deg, the control deck slopes
// ~18 deg toward the player. Three printed parts, no supports needed.
//
//   body   the wedge shell. Screen aperture with a lip the panel rests on
//          from behind, deck opening with bosses, open rear.
//   deck   flat control plate. Sits on top of the deck opening and screws
//          down, so the panel face carries no load.
//   back   rear cover, vented, with a cable exit.
//
//   openscad -D 'part="deck"' -o deck.stl pixy_case.scad
//
// MEASURE THESE before printing -- everything else is derived.
panel_w = 192;   // Waveshare P3 64x32 active area (confirmed)
panel_h = 96;
pcb_t   = 8;     // ESTIMATE: bare PCB depth, no connectors
back_t  = 14;    // ESTIMATE: total depth including the IDC connectors

wall      = 3;
bezel_lip = 4;     // overlap holding the panel in from the front
clear     = 0.4;   // slip fit between printed parts
screw     = 3.2;   // M3 free fit
boss_d    = 7;     // screw boss outside diameter
boss_hole = 2.9;   // self-tapping M3. Use 4.2 for heat-set inserts.

// ── Cabinet geometry ──────────────────────────────────────────────────────
W            = panel_w + 2*(bezel_lip + wall + 2);   // 208
D            = 130;
deck_front_h = 22;
deck_run     = 85;
deck_rise    = 28;
screen_run   = 19;
screen_rise  = 106;

deck_ang   = atan(deck_rise / deck_run);
screen_ang = atan(screen_run / screen_rise);
deck_len   = sqrt(deck_run*deck_run + deck_rise*deck_rise);
H          = deck_front_h + deck_rise + screen_rise;

PROFILE = [[0,0], [D,0], [D,H], [deck_run+screen_run,H],
           [deck_run, deck_front_h+deck_rise], [0, deck_front_h]];

deck_w    = W - 2*wall - 2*clear;     // plate width, across the cabinet
deck_l    = deck_len - 2*wall;        // plate length, up the slope
open_in   = 9;                        // ledge width around the deck opening
scr_in    = 8;                        // screw inset from the plate edge

// ── Placement helpers. Children are in face-local coords, centred. ────────
// Deck local: +X up the slope, +Y across, +Z out of the surface.
module on_deck() {
  translate([deck_run/2, W/2, deck_front_h + deck_rise/2])
    rotate([0, -deck_ang, 0]) children();
}
// Screen local: +Z up the face, +Y across, +X into the cabinet.
module on_screen() {
  translate([deck_run + screen_run/2, W/2,
             deck_front_h + deck_rise + screen_rise/2])
    rotate([0, screen_ang, 0]) children();
}

deck_screws = [for (x = [-1,1], y = [-1,1])
                 [x*(deck_l/2 - scr_in), y*(deck_w/2 - scr_in)]];

// ── Control layout, in deck-local coords ──────────────────────────────────
enc_d       = 7.6;
btn_big_d   = 12.4;
btn_small_d = 7.0;
dpad_r      = 19;

enc1_y = -deck_w/2 + 26;
dpad_y = -deck_w/2 + 72;
ab_y   =  deck_w/2 - 74;
sys_y  =  deck_w/2 - 47;
enc2_y =  deck_w/2 - 26;

module deck_holes_2d() {
  translate([0, enc1_y]) circle(d = enc_d, $fn = 40);
  translate([0, enc2_y]) circle(d = enc_d, $fn = 40);
  for (a = [0:90:270])
    translate([dpad_r*sin(a), dpad_y + dpad_r*cos(a)]) circle(d = btn_big_d, $fn = 40);
  for (x = [-13, 13]) translate([x, ab_y]) circle(d = btn_big_d, $fn = 40);
  for (x = [-15, 15]) translate([x, sys_y]) circle(d = btn_small_d, $fn = 30);
  for (i = [-2:2], j = [-1:1])                       // buzzer grille
    translate([deck_l/2 - 12 + j*4, i*4]) circle(d = 2, $fn = 16);
  for (p = deck_screws) translate(p) circle(d = screw, $fn = 30);
}

// ── Parts ─────────────────────────────────────────────────────────────────
module shell_solid(w) {
  translate([0, w, 0]) rotate([90,0,0]) linear_extrude(w) polygon(PROFILE);
}

module body() {
  difference() {
    union() {
      difference() {
        shell_solid(W);
        // Hollow with a 2D offset, which keeps the wall constant on every
        // sloping face. Scaling the solid would not.
        translate([0, W - wall, 0]) rotate([90,0,0])
          linear_extrude(W - 2*wall) offset(r = -wall) polygon(PROFILE);
        // Open the rear.
        translate([D - wall, -1, -1]) cube([wall+2, W+2, H+2]);
      }
      // Bosses for the deck plate, standing proud on the inside face.
      on_deck() for (p = deck_screws)
        translate([p[0], p[1], -6]) cylinder(d = boss_d, h = 6.5, $fn = 30);
    }
    // Screen: through-window, deliberately smaller than the panel so a
    // bezel_lip of material remains for the panel to press against.
    on_screen() cube([80, panel_w - 2*bezel_lip, panel_h - 2*bezel_lip], center = true);
    // Recess behind it for the panel PCB to drop into.
    on_screen() translate([pcb_t/2 + wall/2, 0, 0])
      cube([pcb_t + wall, panel_w + 2*clear, panel_h + 2*clear], center = true);
    // Deck opening, smaller than the plate so the plate lands on a ledge.
    on_deck() cube([deck_l - 2*open_in, deck_w - 2*open_in, 80], center = true);
    // Pilot holes in the bosses.
    on_deck() for (p = deck_screws)
      translate([p[0], p[1], -8]) cylinder(d = boss_hole, h = 12, $fn = 24);
  }
}

module deck() {
  difference() {
    translate([-deck_l/2, -deck_w/2, 0])
      linear_extrude(wall) offset(r = 2) offset(r = -2) square([deck_l, deck_w]);
    translate([0,0,-1]) linear_extrude(wall + 2) deck_holes_2d();
  }
}

module back() {
  bw = W - 2*wall - 2*clear;
  bh = H - wall;
  difference() {
    linear_extrude(wall) offset(r = 3) offset(r = -3) square([bw, bh]);
    for (i = [0:6], j = [0:9])                       // vents
      translate([26 + i*24, 26 + j*11, -1])
        linear_extrude(wall+2) offset(r = 1.5) square([12, 1], center = true);
    translate([bw/2, 14, -1])                        // cable exit
      linear_extrude(wall+2) offset(r = 4) square([34, 6], center = true);
    for (x = [9, bw-9], y = [9, bh-9])
      translate([x, y, -1]) cylinder(d = screw, h = wall+2, $fn = 30);
  }
}

part = "all";
if      (part == "body") body();
else if (part == "deck") deck();
else if (part == "back") back();
else { body(); translate([-70,0,0]) deck(); translate([-160,0,0]) back(); }
