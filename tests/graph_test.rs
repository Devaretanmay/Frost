use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_work_graph_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("work").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("--graph"));
}
