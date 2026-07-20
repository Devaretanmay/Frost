use crate::core::Project;

pub enum CellRef {
    Goal,
    Capability(usize),
    CenterAlias(usize),
    Task(usize, usize),
}

pub const BLOCK_CENTERS: [(usize, usize); 8] = [
    (1, 4),
    (1, 7),
    (4, 7),
    (7, 7),
    (7, 4),
    (7, 1),
    (4, 1),
    (1, 1),
];

pub const CENTER_RING: [(usize, usize); 8] = [
    (3, 4),
    (3, 5),
    (4, 5),
    (5, 5),
    (5, 4),
    (5, 3),
    (4, 3),
    (3, 3),
];

fn block_center(r: usize, c: usize) -> (usize, usize) {
    ((r / 3) * 3 + 1, (c / 3) * 3 + 1)
}

pub fn pos_to_ref(r: usize, c: usize) -> CellRef {
    if r == 4 && c == 4 {
        return CellRef::Goal;
    }
    for (i, &(br, bc)) in BLOCK_CENTERS.iter().enumerate() {
        if r == br && c == bc {
            return CellRef::Capability(i);
        }
    }
    for (i, &(cr, cc)) in CENTER_RING.iter().enumerate() {
        if r == cr && c == cc {
            return CellRef::CenterAlias(i);
        }
    }
    let (br, bc) = block_center(r, c);
    for (i, &(bcr, bcc)) in BLOCK_CENTERS.iter().enumerate() {
        if br == bcr && bc == bcc {
            let local = |pos: usize, center: usize| -> usize {
                if pos < center {
                    0
                } else if pos == center {
                    1
                } else {
                    2
                }
            };
            let lr = local(r, br);
            let lc = local(c, bc);
            let ti = lr * 3 + lc;
            let ti = if ti > 4 { ti - 1 } else { ti };
            return CellRef::Task(i, ti);
        }
    }
    CellRef::Goal
}

pub fn cell_title(proj: &Project, r: usize, c: usize) -> String {
    match pos_to_ref(r, c) {
        CellRef::Goal => proj.goal.clone(),
        CellRef::Capability(i) => proj.capabilities[i].cell.title.clone(),
        CellRef::CenterAlias(i) => proj.capabilities[i].cell.title.clone(),
        CellRef::Task(ci, ti) => proj.capabilities[ci].tasks[ti].title.clone(),
    }
}

pub fn cell_status(proj: &Project, r: usize, c: usize) -> &crate::core::Status {
    match pos_to_ref(r, c) {
        CellRef::Goal => &crate::core::Status::Completed,
        CellRef::Capability(i) => &proj.capabilities[i].cell.status,
        CellRef::CenterAlias(i) => &proj.capabilities[i].cell.status,
        CellRef::Task(ci, ti) => &proj.capabilities[ci].tasks[ti].status,
    }
}

pub fn cell_mut(proj: &mut Project, r: usize, c: usize) -> &mut crate::core::Cell {
    match pos_to_ref(r, c) {
        CellRef::Capability(i) => &mut proj.capabilities[i].cell,
        CellRef::CenterAlias(i) => &mut proj.capabilities[i].cell,
        CellRef::Task(ci, ti) => &mut proj.capabilities[ci].tasks[ti],
        CellRef::Goal => panic!("goal cell is read-only"),
    }
}
