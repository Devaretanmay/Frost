use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_compile_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("compile").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("--from-issue"))
        .stdout(predicate::str::contains("--from-diff"))
        .stdout(predicate::str::contains("--from-rfc"));
}

#[test]
fn test_compile_plain_goal() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("compile").arg("My plain goal");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("Goal: My plain goal"))
        .stdout(predicate::str::contains("Context:").not());
}
