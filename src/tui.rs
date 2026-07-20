use anyhow::Result;
use crossterm::event::{self, Event, KeyCode};
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
};
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span, Text};
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};
use ratatui::{backend::CrosstermBackend, Frame, Terminal};
use std::io::{self, Write};

use crate::core::{Project, Status};
use crate::layout::{self, BLOCK_CENTERS};

fn status_color(s: &Status) -> Color {
    match s {
        Status::Completed => Color::Green,
        Status::InProgress => Color::Yellow,
        Status::Pending | Status::Waiting => Color::DarkGray,
        Status::Failed => Color::Red,
        Status::NeedsReview => Color::LightYellow,
        Status::Blocked => Color::Red,
        Status::NotRequired | Status::Skipped | Status::Cancelled => Color::Gray,
    }
}

fn short(s: &str, n: usize) -> String {
    if s.len() <= n {
        s.to_string()
    } else {
        format!("{}…", &s[..n - 1])
    }
}

fn grid_ui(f: &mut Frame, proj: &Project, sr: usize, sc: usize, area: Rect) {
    let mut lines: Vec<Line> = Vec::new();
    for r in 0..9 {
        let mut spans: Vec<Span> = Vec::new();
        for c in 0..9 {
            let status = layout::cell_status(proj, r, c);
            let title = layout::cell_title(proj, r, c);
            let mut st = Style::default().bg(status_color(status));
            if r == sr && c == sc {
                st = Style::default()
                    .bg(Color::Blue)
                    .fg(Color::White)
                    .add_modifier(Modifier::BOLD);
            } else {
                st = st.fg(Color::Black).add_modifier(Modifier::BOLD);
            }
            let label = short(&title, 5);
            let display = format!(" {:<5} ", label);
            spans.push(Span::styled(display, st));
            if c == 2 || c == 5 {
                spans.push(Span::raw(" "));
            }
        }
        lines.push(Line::from(spans));
        if r == 2 || r == 5 {
            lines.push(Line::from(Span::raw("")));
        }
    }
    let widget = Paragraph::new(Text::from(lines)).block(
        Block::default()
            .borders(Borders::ALL)
            .title(" 9x9 Mandala "),
    );
    f.render_widget(widget, area);
}

fn detail_ui(f: &mut Frame, proj: &Project, sr: usize, sc: usize, area: Rect) {
    let title = layout::cell_title(proj, sr, sc);
    let status = layout::cell_status(proj, sr, sc);
    let role = match layout::pos_to_ref(sr, sc) {
        layout::CellRef::Goal => "GOAL",
        layout::CellRef::Capability(_) | layout::CellRef::CenterAlias(_) => "CAPABILITY",
        layout::CellRef::Task(_, _) => "TASK",
    };
    let (done, total) = proj.task_count();
    let pct = done.checked_mul(100).and_then(|v| v.checked_div(total)).unwrap_or(0);

    let mut info = format!(" ({},{}) {} — {}  {:?}", sr, sc, role, title, status);
    if let layout::CellRef::Task(ci, ti) = layout::pos_to_ref(sr, sc) {
        let cell = &proj.capabilities[ci].tasks[ti];
        info.push_str(&format!(
            "\n Assigned: {:?} {}  Criteria: {}  Validation: {}",
            cell.assigned_to.kind,
            cell.assigned_to.name,
            cell.completion_criteria.join(", "),
            cell.validation_criteria.join(", ")
        ));
        info.push_str(&format!("\n Notes: {}", cell.notes));
    }
    if let layout::CellRef::Capability(i) | layout::CellRef::CenterAlias(i) =
        layout::pos_to_ref(sr, sc)
    {
        let (cd, ct) = proj.cap_progress(i);
        info.push_str(&format!(
            "\n Progress: {}/{}  Capability complete: {}",
            cd,
            ct,
            if cd == ct { "YES" } else { "no" }
        ));
    }
    info.push_str(&format!(
        "\n\n Project: {}/{} ({})  Enter:drill  Space:toggle  e:edit  q:quit",
        done, total, pct
    ));
    let widget = Paragraph::new(info)
        .block(Block::default().borders(Borders::ALL).title(" Detail "))
        .wrap(Wrap { trim: false });
    f.render_widget(widget, area);
}

fn prompt_edit(msg: &str, current: &str) -> Result<String> {
    disable_raw_mode()?;
    crossterm::execute!(io::stdout(), LeaveAlternateScreen)?;
    let result = {
        print!("{} [{}]: ", msg, current);
        io::stdout().flush()?;
        let mut s = String::new();
        io::stdin().read_line(&mut s)?;
        let trimmed = s.trim().to_string();
        if trimmed.is_empty() {
            current.to_string()
        } else {
            trimmed
        }
    };
    enable_raw_mode()?;
    crossterm::execute!(io::stdout(), EnterAlternateScreen)?;
    Ok(result)
}

pub fn run(proj: &mut Project) -> Result<()> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    crossterm::execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let (mut sr, mut sc) = (4usize, 4usize);

    let res = loop {
        terminal.draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(1),
                    Constraint::Min(3),
                    Constraint::Length(8),
                ])
                .split(f.area());
            let header = Paragraph::new(format!(" Harada — {}", proj.goal)).style(
                Style::default()
                    .fg(Color::Cyan)
                    .add_modifier(Modifier::BOLD),
            );
            f.render_widget(header, chunks[0]);
            grid_ui(f, proj, sr, sc, chunks[1]);
            detail_ui(f, proj, sr, sc, chunks[2]);
        })?;

        if let Event::Key(k) = event::read()? {
            match k.code {
                KeyCode::Char('q') => break Ok(()),
                KeyCode::Up if sr > 0 => sr -= 1,
                KeyCode::Down if sr < 8 => sr += 1,
                KeyCode::Left if sc > 0 => sc -= 1,
                KeyCode::Right if sc < 8 => sc += 1,
                KeyCode::Enter => {
                    if let layout::CellRef::CenterAlias(i) = layout::pos_to_ref(sr, sc) {
                        (sr, sc) = BLOCK_CENTERS[i];
                    }
                }
                KeyCode::Char(' ') => {
                    let status = layout::cell_status(proj, sr, sc);
                    if status != &Status::Completed || true {
                        let cell = layout::cell_mut(proj, sr, sc);
                        cell.status = cell.status.cycle();
                    }
                }
                KeyCode::Char('e') => {
                    let title = layout::cell_title(proj, sr, sc);
                    if let Ok(new) = prompt_edit("Edit title", &title) {
                        let cell = layout::cell_mut(proj, sr, sc);
                        cell.title = new;
                    }
                }
                _ => {}
            }
        }
    };
    disable_raw_mode()?;
    crossterm::execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;
    res
}
