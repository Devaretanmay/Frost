use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_stats_badge_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("stats").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("--badge"));
}

#[test]
fn test_cli_init_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("init").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("--github-action"))
        .stdout(predicate::str::contains("--pre-commit"));
}

#[test]
fn test_cli_work_notify_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("work").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("--notify <NOTIFY>"));
}
