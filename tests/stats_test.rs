use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_stats_advanced_help() {
    let mut cmd = Command::cargo_bin("harada").unwrap();
    cmd.arg("stats").arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("--badge"))
        .stdout(predicate::str::contains("--export <EXPORT>"))
        .stdout(predicate::str::contains("--since <SINCE>"));
}
