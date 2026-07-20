use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_assign_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("assign").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("--tool <TOOL>"))
        .stdout(predicate::str::contains("--suggest"));
}

#[test]
fn test_cli_handoff_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("handoff").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("Generate a prompt handoff"))
        .stdout(predicate::str::contains(
            "--export-handoff <EXPORT_HANDOFF>",
        ));
}
