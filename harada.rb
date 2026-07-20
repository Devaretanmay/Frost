class Harada < Formula
  desc "A Dev-First Execution OS that turns goals into 1x8x8 grids of tasks"
  homepage "https://github.com/example/harada"
  version "1.0.0-rc1"

  if OS.mac? && Hardware::CPU.intel?
    url "https://github.com/example/harada/releases/download/v1.0.0-rc1/harada-macos-x86_64"
    sha256 "REPLACE_WITH_SHA256"
  elsif OS.mac? && Hardware::CPU.arm?
    url "https://github.com/example/harada/releases/download/v1.0.0-rc1/harada-macos-arm64"
    sha256 "REPLACE_WITH_SHA256"
  elsif OS.linux? && Hardware::CPU.intel?
    url "https://github.com/example/harada/releases/download/v1.0.0-rc1/harada-linux-x86_64"
    sha256 "REPLACE_WITH_SHA256"
  end

  def install
    if OS.mac? && Hardware::CPU.intel?
      bin.install "harada-macos-x86_64" => "harada"
    elsif OS.mac? && Hardware::CPU.arm?
      bin.install "harada-macos-arm64" => "harada"
    elsif OS.linux? && Hardware::CPU.intel?
      bin.install "harada-linux-x86_64" => "harada"
    end
  end

  test do
    system "#{bin}/harada", "--version"
  end
end
