//! The max-level aura under a unit's feet. The client draws it itself from textured quads, not from effect files:
//! - level 99: two pulsing glows on the ground and three tilted ribbons turning round the body (EF_LEVEL99), and 16
//!   motes rising from the feet (EF_LEVEL99_ORB1, or ORB2 for babies);
//! - 3rd jobs and the expanded classes at 200 (red, EF_LEVEL185), 4th jobs and homunculi at 275 (orange,
//!   EF_LEVEL4TH): walls of bubbles rising and opening outward with two pulsing discs on the ground, and four shock
//!   rings spreading over the ground (the _SUB effect).
//!
//! Sizes are in world units (5 a cell).

use rustnarok_client::grf::Grf;

use crate::render::{Gpu, Texture};
use crate::world::{EffectMesh, EffectQuad, MeshVertex, Vector};

/// The client moves the aura on in steps of 16 ms; the rates below are per step.
const STEP_SECONDS: f32 = 0.016;
/// Sprite pixels to a world unit (35 a cell of 5).
const PIXELS: f32 = 7.0;
/// Not drawn farther than this from the player, in cells.
pub const SEEN_CELLS: f32 = 26.0;

pub struct Textures {
    glow: Option<Texture>,
    ribbon: Option<Texture>,
    mote: Option<Texture>,
    baby_mote: Option<Texture>,
    /// The walls' 22 pieces round a circle (W_bubble01 to 22), and the discs and rings.
    bubbles: Vec<Option<Texture>>,
    disc: Option<Texture>,
    shock: Option<Texture>,
    slayer_wisp: Texture,
}

impl Textures {
    pub fn load(gpu: &Gpu, grf: &Grf) -> Self {
        let load = |name: &str| gpu.try_load_texture(grf, &format!("data\\texture\\effect\\{name}"), true).ok();
        Self {
            glow: load("pikapika2.bmp"),
            ribbon: load("ring_blue.tga"),
            mote: load("whitelight.tga"),
            baby_mote: load("freezing_circle.bmp"),
            bubbles: (1..=22).map(|piece| load(&format!("W_bubble{piece:02}.tga"))).collect(),
            disc: load("cir0002.tga"),
            shock: load("emp shock.tga"),
            slayer_wisp: gpu.texture(&image::RgbaImage::from_fn(64, 64, |x, y| {
                let x = (x as f32 - 31.5) / 31.5;
                let y = (y as f32 - 31.5) / 31.5;
                let radius = (x*x + y*y).sqrt();
                let falloff = (1.0 - radius).max(0.0).powf(1.7);
                let turbulence = 0.7 + 0.3 * (x*9.0 + y*7.0 + (y*12.0).sin()).sin();
                image::Rgba([255, 255, 255, (255.0 * falloff * turbulence) as u8])
            }), true),
        }
    }
}

/// A max-level aura.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Kind {
    /// Level 99; a baby's motes are its own.
    Level99 { baby: bool },
    /// 3rd jobs and the expanded classes at 200: red (EF_LEVEL185).
    Level185,
    /// 4th jobs and homunculi at 275: orange (EF_LEVEL4TH).
    Fourth,
}

/// The aura a unit of sprite job `job` at `level` has, if any: only at exactly its job group's top level, the groups
/// tried in the client's order. Monsters never have one.
pub fn kind(job: u16, level: u16) -> Option<Kind> {
    let third = matches!(job, 4054..=4112 | 4120 | 4127 | 4129 | 4132 | 4133 | 4140 | 4143 | 4148 | 4151 | 4173..=4180 | 4182 | 4197 | 4198)
        || matches!(job, 4201 | 4202 | 4205 | 4206 | 4208 | 4209);
    let fourth = matches!(job, 4252..=4299 | 4302..=4329 | 4355 | 4360);
    let expanded = matches!(job, 4190..=4193 | 4211..=4216 | 4223 | 4224 | 4229 | 4231 | 4232 | 4237 | 4239..=4248 | 4353 | 4354 | 4359 | 4217..=4221);
    let homunculus = matches!(job, 6001..=6016 | 6048..=6052);
    let monster = matches!(job, 1001..=3998 | 20021..=31999);
    let baby = matches!(job, 4023..=4045 | 4158..=4182 | 4222..=4238);
    match level {
        200 if third || (expanded && !fourth) => Some(Kind::Level185),
        275 if fourth || homunculus => Some(Kind::Fourth),
        99 if !(third || fourth || expanded || monster || matches!(job, 6048..=6052)) => Some(Kind::Level99 { baby }),
        _ => None,
    }
}

/// Draws a unit's aura at `feet`, `seconds` into the map; `seed` scatters what's random in it. `full` (`/aura` on): the
/// whole aura, else only its lesser part (the motes, the shock rings).
#[allow(clippy::too_many_arguments)]
pub fn draw<'a>(
    textures: &'a Textures,
    kind: Kind,
    feet: Vector,
    seconds: f32,
    seed: u32,
    full: bool,
    meshes: &mut Vec<EffectMesh<'a>>,
    quads: &mut Vec<EffectQuad<'a>>,
) {
    match kind {
        Kind::Level99 { baby } => draw99(textures, feet, baby, seconds, seed, full, meshes, quads),
        Kind::Level185 => draw_high(textures, feet, &RED, seconds, seed, full, meshes),
        Kind::Fourth => draw_high(textures, feet, &ORANGE, seconds, seed, full, meshes),
    }
}

/// MYGENE_SLAYER456_ART: own equipped relic aura, independent of Base Level 99.
/// The dark relic uses ordinary alpha blending, not additive black (invisible).
pub fn draw_slayer<'a>(textures: &'a Textures, item: u32, feet: Vector, seconds: f32,
    quads: &mut Vec<EffectQuad<'a>>) {
    let (color, additive, count) = match item {
        31004 => ([1.0, 0.78, 0.05], true, 14),
        31008 => ([1.0, 0.06, 0.08], true, 14),
        60012 => ([0.08, 0.42, 1.0], true, 14),
        60015 => ([0.68, 0.23, 1.0], true, 14),
        60018 => ([1.0, 0.43, 0.05], true, 14),
        60021 => ([0.065, 0.045, 0.08], false, 22),
        _ => return,
    };
    for n in 0..count {
        let phase = n as f32 / count as f32;
        let life = (seconds * 0.66 + phase).fract();
        let angle = seconds * 1.45 + phase * std::f32::consts::TAU * 3.0;
        let radius = 2.4 + life * 1.8;
        let centre = [feet[0] + angle.cos()*radius, feet[1] + 0.5 + life*11.0,
            feet[2] + angle.sin()*radius];
        let half = if additive { 8.0 + life*7.0 } else { 12.0 + life*11.0 };
        let fade = (life*std::f32::consts::PI).sin() * if additive { 0.85 } else { 0.90 };
        let corners = [[-half,-half], [half,-half], [half,half], [-half,half]];
        quads.push((&textures.slayer_wisp, centre, corners,
            [color[0], color[1], color[2], fade], additive, false));
    }
}

/// MYGENE_ARCANE_VISUAL_V7. Cosmetic only; all damage comes from the map server.
pub fn draw_arcane<'a>(
    textures: &'a Textures, kind: u32, from: Vector, to: Vector, age: f32,
    ground: &impl Fn(f32, f32) -> f32,
    quads: &mut Vec<EffectQuad<'a>>, meshes: &mut Vec<EffectMesh<'a>>,
) {
    let color = match kind {
        10 => [0.15, 0.48, 1.0],
        11 | 13 => [0.73, 0.20, 1.0],
        12 | 14 => [1.0, 0.40, 0.04],
        _ => return,
    };
    let texture = &textures.slayer_wisp;
    let mut glow = |at: Vector, half: f32, rgb: [f32; 3], opacity: f32| {
        let corners = [[-half, -half], [half, -half], [half, half], [-half, half]];
        quads.push((texture, at, corners,
            [rgb[0], rgb[1], rgb[2], opacity.clamp(0.0, 1.0)], true, false));
    };

    if kind <= 12 {
        // A short flight with a tapered energy trail; a brighter head and impact.
        let flight = 0.22_f32;
        if age < flight {
            let t = (age / flight).clamp(0.0, 1.0);
            let head = |p: f32| -> Vector {
                [from[0] + (to[0] - from[0]) * p,
                 from[1] + (to[1] - from[1]) * p + 5.0 + 2.0 * (p * std::f32::consts::PI).sin(),
                 from[2] + (to[2] - from[2]) * p]
            };
            let size = match kind { 10 => 8.0, 11 => 18.0, _ => 13.0 };
            for i in (1..=6).rev() {
                let q = (t - i as f32 * 0.035).max(0.0);
                let fade = 1.0 - i as f32 / 7.0;
                glow(head(q), size * fade, color, fade * 0.8);
            }
            let at = head(t);
            glow(at, size, color, 0.95);
            glow(at, size * 0.43, [1.0, 0.95, 0.9], 0.95);
        } else if age < 0.42 {
            let p = ((age - flight) / 0.20).clamp(0.0, 1.0);
            let at = [to[0], to[1] + 5.0, to[2]];
            glow(at, 12.0 + 23.0 * p, color, (1.0 - p) * 0.8);
        }
        return;
    }

    // Burst cues are emitted only when the server schedules secondary damage.
    let p = (age - 0.20) / 0.46;
    if !(0.0..1.0).contains(&p) { return; }
    let opacity = (p * std::f32::consts::PI).sin();
    let mut triangles = Vec::new();
    for dz in -1_i32..=1 {
        for dx in -1_i32..=1 {
            if kind == 13 && dx.abs() + dz.abs() > 1 { continue; }
            let x = to[0] + dx as f32 * crate::world::CELL;
            let z = to[2] + dz as f32 * crate::world::CELL;
            let y = ground(x, z);
            let at = [x, y, z];
            let tint = [color[0], color[1], color[2], opacity * 0.72];
            triangles.extend(flat(at, 2.3, 0.0, tint));
            triangles.extend(flat(at, 2.3, 180.0, tint));
            glow([x, y + 1.0 + p * 8.0, z],
                11.0 + p * 15.0, color, opacity * 0.8);
        }
    }
    meshes.push((texture, triangles, true));
}

/// A high aura's colours: the bubble walls, the two discs, and the four shock rings.
struct Colors {
    walls: [u8; 3],
    discs: [[u8; 3]; 2],
    rings: [[u8; 3]; 4],
}

const RED: Colors =
    Colors { walls: [255, 155, 155], discs: [[255, 55, 55], [255, 155, 155]], rings: [[255, 105, 105], [255, 5, 5], [255, 55, 55], [255, 155, 155]] };
const ORANGE: Colors = Colors { walls: [255, 155, 0], discs: [[255, 155, 0]; 2], rings: [[255, 155, 0]; 4] };

fn tint([red, green, blue]: [u8; 3], alpha: f32) -> [f32; 4] {
    [f32::from(red) / 255.0, f32::from(green) / 255.0, f32::from(blue) / 255.0, alpha / 255.0]
}

/// A flat square on the ground at `feet`, `half` across each way, turned `degrees`.
fn flat(feet: Vector, half: f32, degrees: f32, tint: [f32; 4]) -> [MeshVertex; 6] {
    let (sin, cos) = degrees.to_radians().sin_cos();
    let corner = |x: f32, z: f32, uv: [f32; 2]| MeshVertex { position: [feet[0] + x * cos + z * sin, feet[1] + 0.2, feet[2] - x * sin + z * cos], uv, tint };
    let [a, b, c, d] = [corner(-half, -half, [0.0, 0.0]), corner(half, -half, [1.0, 0.0]), corner(half, half, [1.0, 1.0]), corner(-half, half, [0.0, 1.0])];
    [a, b, c, a, c, d]
}

/// A bubble wall `steps` in, from its first alpha: its radius, lean (degrees above the ground) and alpha. It starts
/// 3.5 across, leaning 80°, and fades 3 a step; then it starts over again and again: radius 2.87 growing 0.07 a step,
/// lean 74° falling 1° a step, alpha rising 10 a step until the radius is 3.5, then falling 3 to nothing (39 steps).
fn wall_at(first_alpha: f32, steps: f32) -> (f32, f32, f32) {
    let first = first_alpha / 3.0;
    if steps < first {
        return (3.5 + 0.07 * steps, (80.0 - steps).max(10.0), first_alpha - 3.0 * steps);
    }
    let t = (steps - first) % 39.0;
    let alpha = if t <= 9.0 { 10.0 * t } else { 90.0 - 3.0 * (t - 9.0) };
    (2.87 + 0.07 * t, 74.0 - t, alpha.max(0.0))
}

/// A shock ring `steps` after it began: its half size, its alpha, and which round it is (to turn it anew each time).
/// It grows ×1.02 a step from 10; past 20 it fades 3 a step from 200, then starts over at 10 (about 102 steps).
fn ring_at(steps: f32) -> (f32, f32, u32) {
    let grow = 2f32.ln() / 1.02f32.ln();
    let period = grow + 200.0 / 3.0;
    let t = steps % period;
    let size = 10.0 * 1.02f32.powf(t);
    let alpha = if t <= grow { 200.0 } else { 200.0 - 3.0 * (t - grow) };
    (size, alpha.max(0.0), (steps / period) as u32)
}

/// The red or orange aura: two sets of four bubble walls round the body and two pulsing discs (with `full`), and four
/// shock rings spreading over the ground 20 steps apart.
fn draw_high<'a>(textures: &'a Textures, feet: Vector, colors: &Colors, seconds: f32, seed: u32, full: bool, meshes: &mut Vec<EffectMesh<'a>>) {
    let steps = seconds / STEP_SECONDS;
    if full {
        // Each wall: 22 pieces round the circle, piece k in W_bubble k; sunk 5 under the feet; its top waving
        // (30 - n)·(1 + 0.15·sin 9k°) high. The second set fades in after the first.
        let mut pieces: Vec<Vec<MeshVertex>> = vec![Vec::new(); 22];
        for alphas in [[180.0, 135.0, 90.0, 45.0], [160.0, 115.0, 70.0, 25.0]] {
            for (n, (first_alpha, turn)) in alphas.into_iter().zip([180.0f32, 270.0, 0.0, 90.0]).enumerate() {
                let (radius, lean, alpha) = wall_at(first_alpha, steps);
                if alpha <= 0.0 {
                    continue;
                }
                let tint = tint(colors.walls, alpha);
                let lean = lean.to_radians();
                let edge = |k: usize| {
                    let (sin, cos) = (turn + 360.0 * k as f32 / 22.0).to_radians().sin_cos();
                    let height = (30.0 - n as f32) * (1.0 + 0.15 * (9.0 * k as f32).to_radians().sin());
                    let out = radius + height * lean.cos();
                    let u = k as f32 / 22.0;
                    (
                        MeshVertex { position: [feet[0] + sin * radius, feet[1] - 5.0, feet[2] + cos * radius], uv: [u, 1.0], tint },
                        MeshVertex { position: [feet[0] + sin * out, feet[1] - 5.0 + height * lean.sin(), feet[2] + cos * out], uv: [u, 0.0], tint },
                    )
                };
                for (k, piece) in pieces.iter_mut().enumerate() {
                    let ((low, high), (next_low, next_high)) = (edge(k), edge(k + 1));
                    piece.extend([low, high, next_low, high, next_high, next_low]);
                }
            }
        }
        for (texture, triangles) in textures.bubbles.iter().zip(pieces) {
            if let Some(texture) = texture
                && !triangles.is_empty()
            {
                meshes.push((texture, triangles, true));
            }
        }
        // The discs: cir0002 18 and emp shock 11 across, pulsing 0.8·size + 1 + 0.1·size·sin φ, each as two flat
        // squares turned 0° and 180°.
        let phase = (3.0 * steps).to_radians().sin();
        for (texture, size, color) in [(&textures.disc, 18.0, colors.discs[0]), (&textures.shock, 11.0, colors.discs[1])] {
            let Some(texture) = texture else { continue };
            let half = 0.8 * size + 1.0 + 0.1 * size * phase;
            let tint = tint(color, 200.0);
            meshes.push((texture, [flat(feet, half, 0.0, tint), flat(feet, half, 180.0, tint)].concat(), true));
        }
    }
    // The shock rings: four layers 20 steps apart, each two flat squares at a turn drawn anew every round.
    let Some(shock) = &textures.shock else { return };
    let mut triangles = Vec::new();
    for (layer, color) in colors.rings.into_iter().enumerate() {
        let since = steps - 20.0 * layer as f32;
        if since < 0.0 {
            continue;
        }
        let (half, alpha, round) = ring_at(since);
        let turn = (seed.wrapping_mul(31).wrapping_add(layer as u32 * 97).wrapping_add(round.wrapping_mul(2_654_435_761)) >> 4) % 360;
        let tint = tint(color, alpha);
        triangles.extend(flat(feet, half, turn as f32, tint));
        triangles.extend(flat(feet, half, turn as f32 + 180.0, tint));
    }
    meshes.push((shock, triangles, true));
}

/// The level-99 aura; see `draw`.
#[allow(clippy::too_many_arguments)]
fn draw99<'a>(
    textures: &'a Textures,
    feet: Vector,
    baby: bool,
    seconds: f32,
    seed: u32,
    full: bool,
    meshes: &mut Vec<EffectMesh<'a>>,
    quads: &mut Vec<EffectQuad<'a>>,
) {
    let steps = seconds / STEP_SECONDS;
    let at = |x: f32, up: f32, z: f32| [feet[0] + x, feet[1] + up, feet[2] + z];
    let vertex = |position: Vector, uv: [f32; 2], tint: [f32; 4]| MeshVertex { position, uv, tint };
    if full && let Some(glow) = &textures.glow {
        // Two flat glows turned 0° and 22°, pulsing 9 to 10.8 units half across, half a pulse apart.
        let tint = [1.0, 1.0, 1.0, 200.0 / 255.0];
        let mut triangles = Vec::new();
        for (turn, phase) in [(0f32, 0f32), (22.0, 180.0)] {
            let size = 9.0 + 0.9 * ((phase + 3.0 * steps).to_radians().sin() + 1.0);
            let (sin, cos) = turn.to_radians().sin_cos();
            let corner = |x: f32, z: f32, uv: [f32; 2]| vertex(at(x * cos + z * sin, 0.2, -x * sin + z * cos), uv, tint);
            let [a, b, c, d] =
                [corner(-size, -size, [0.0, 0.0]), corner(size, -size, [1.0, 0.0]), corner(size, size, [1.0, 1.0]), corner(-size, size, [0.0, 1.0])];
            triangles.extend([a, b, c, a, c, d]);
        }
        meshes.push((glow, triangles, true));
    }
    if full && let Some(ribbon) = &textures.ribbon {
        // Three ribbons over 315° arcs (22 points 15° apart), rising and falling along the arc, leaning outward,
        // turning 3, 4 and 5° a step.
        let tint = [100.0 / 255.0, 100.0 / 255.0, 1.0, 120.0 / 255.0];
        let mut triangles = Vec::new();
        for i in 0..3 {
            let band = i as f32;
            let (radius, height, tilt) = (3.9 + 0.2 * band, 15.0 - 2.0 * band, (55.0 - 5.0 * band).to_radians());
            let start = 90.0 * band + (3.0 + band) * steps;
            let column = |s: usize| {
                let (sin, cos) = (start + 15.0 * s as f32).to_radians().sin_cos();
                let rise = (height * (9.0 * s as f32).to_radians().sin()).max(0.0);
                let out = radius + rise * tilt.cos();
                let u = s as f32 / 21.0;
                (vertex(at(sin * radius, 0.0, cos * radius), [u, 1.0], tint), vertex(at(sin * out, rise * tilt.sin(), cos * out), [u, 0.0], tint))
            };
            for s in 0..21 {
                let ((low, high), (next_low, next_high)) = (column(s), column(s + 1));
                triangles.extend([low, high, next_low, high, next_high, next_low]);
            }
        }
        meshes.push((ribbon, triangles, true));
    }
    let (texture, size, color) = if baby { (&textures.baby_mote, 0.55, [1.0, 1.0, 1.0]) } else { (&textures.mote, 1.8, [80.0 / 255.0, 80.0 / 255.0, 1.0]) };
    let Some(texture) = texture else { return };
    for mote in 0..16 {
        // Each mote's own wait (up to 100/0.15 steps), start and wander, from the unit and its number.
        let id = seed.wrapping_mul(16).wrapping_add(mote);
        let random = |salt: u32| (id.wrapping_mul(2_654_435_761).wrapping_add(salt.wrapping_mul(40_503)) >> 8) % 1000;
        let (rise, alpha, drift) = mote_at((random(1) % 100) as f32 / 0.15, steps + random(2) as f32, random(3) as f32);
        if alpha <= 0.0 {
            continue;
        }
        let half = size * PIXELS;
        let corners = [[-half, -half], [half, -half], [half, half], [-half, half]];
        quads.push((texture, at(drift[0], rise, drift[1]), corners, [color[0], color[1], color[2], alpha], true, false));
    }
}

/// A mote `steps` into its cycle: how high it is, how opaque (0: waiting, unseen), and how far it wandered. It waits
/// `wait` steps at the feet, then rises 0.15 a step, fully opaque to 20 units and fading 4/255 a step after, and
/// starts again above 30.
// ponytail: each mote keeps one wait and wanders on two sine waves; the client draws a new wait each time and steers
// its drift toward random targets.
fn mote_at(wait: f32, steps: f32, phase: f32) -> (f32, f32, [f32; 2]) {
    let t = steps % (wait + 30.0 / 0.15);
    if t < wait {
        return (0.0, 0.0, [0.0; 2]);
    }
    let rise = (t - wait) * 0.15;
    let alpha = if rise <= 20.0 { 1.0 } else { (255.0 - 4.0 * (rise - 20.0) / 0.15).max(0.0) / 255.0 };
    let drift = [2.0 * (t * 0.05 + phase).sin(), 2.0 * (t * 0.04 + phase * 1.7).sin()];
    (rise, alpha, drift)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shows_at_the_groups_top_level() {
        let level99 = |baby| Some(Kind::Level99 { baby });
        assert_eq!(kind(0, 99), level99(false), "a Novice at 99");
        assert_eq!(kind(4008, 99), level99(false), "a Lord Knight");
        assert_eq!(kind(4030, 99), level99(true), "a baby Knight: the baby's motes");
        assert_eq!(kind(6005, 99), level99(false), "a homunculus at 99");
        assert_eq!([kind(7, 98), kind(4054, 99), kind(1002, 99), kind(4060, 199)], [None; 4], "below 99, a 3rd job at 99, a monster, 199");
        // 3rd jobs (and their babies) and the expanded classes at 200; 4th jobs and homunculi at 275.
        assert_eq!([kind(4054, 200), kind(4096, 200), kind(4211, 200), kind(4218, 200), kind(4190, 200)], [Some(Kind::Level185); 5]);
        assert_eq!([kind(4252, 275), kind(4308, 275), kind(6050, 275), kind(6001, 275)], [Some(Kind::Fourth); 4]);
        assert_eq!([kind(4252, 200), kind(6050, 99)], [None; 2], "a 4th job at 200, a homunculus S at 99");
    }

    #[test]
    fn walls_rise_open_and_fade_again() {
        // First: 3.5 across leaning 80°, fading 3 a step from its first alpha.
        assert_eq!(wall_at(180.0, 0.0), (3.5, 80.0, 180.0));
        let (_, lean, alpha) = wall_at(180.0, 30.0);
        assert!((lean - 50.0).abs() < 1e-4 && (alpha - 90.0).abs() < 1e-4);
        // Then rounds of 39 steps: rising 10 a step to 90 (radius 3.5 at step 9), falling 3 to nothing.
        let (radius, lean, alpha) = wall_at(180.0, 60.0 + 9.0);
        assert!((radius - 3.5).abs() < 1e-4 && (lean - 65.0).abs() < 1e-4 && (alpha - 90.0).abs() < 1e-4);
        assert!(wall_at(180.0, 60.0 + 38.9).2 < 1.0);
        // Shock rings: 10 to 20 at full 200, then fading; again after about 102 steps.
        assert_eq!(ring_at(0.0), (10.0, 200.0, 0));
        let (size, alpha, _) = ring_at(35.0);
        assert!((size - 20.0).abs() < 0.1 && (alpha - 200.0).abs() < 1e-3);
        assert_eq!(ring_at(103.0).2, 1);
    }

    #[test]
    fn motes_wait_then_rise_and_fade() {
        // Waiting 100 steps: unseen. Then rising 0.15 a step, opaque to 20 units, fading after; again after 300.
        assert_eq!(mote_at(100.0, 50.0, 0.0).1, 0.0);
        let (rise, alpha, _) = mote_at(100.0, 200.0, 0.0);
        assert!((rise - 15.0).abs() < 1e-3 && alpha == 1.0);
        let (rise, alpha, _) = mote_at(100.0, 260.0, 0.0);
        assert!((rise - 24.0).abs() < 1e-3 && (alpha - (255.0 - 4.0 * 4.0 / 0.15) / 255.0).abs() < 1e-3);
        assert_eq!(mote_at(100.0, 350.0, 0.0).1, 0.0);
    }
}
