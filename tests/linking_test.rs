use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_link_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("link").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("Link a task to a git artifact"));
}

#[test]
fn test_cli_sync_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("sync").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("Sync task states against git/CI"));
}

#[test]
fn test_cli_work_mark_done_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("work").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("--mark-done <MARK_DONE>"));
}
