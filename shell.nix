{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.pandas
    pkgs.python3Packages.plotly
    pkgs.python3Packages.streamlit
    pkgs.python3Packages.rapidfuzz
  ];
}
