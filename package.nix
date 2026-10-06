{
  lib,
  stdenv,
  rustPlatform,
  pkg-config,
  wrapGAppsHook4,
  makeWrapper,
  gtk4,
  gtksourceview5,
  poppler,
  glib,
  pango,
  cairo,
  gdk-pixbuf,
  bubblewrap,
  fontconfig,
  gst_all_1,
  ffmpeg,
}:

rustPlatform.buildRustPackage rec {
  pname = "strata";
  version = "0.21.0";

  src = ./.;

  cargoLock = {
    lockFile = ./Cargo.lock;
  };

  nativeBuildInputs = [
    pkg-config
    wrapGAppsHook4
    makeWrapper
    glib
  ];

  buildInputs = [
    gtk4
    gtksourceview5
    poppler
    glib
    pango
    cairo
    gdk-pixbuf
    fontconfig
    gst_all_1.gstreamer
    gst_all_1.gst-plugins-base
    gst_all_1.gst-plugins-good
    gst_all_1.gst-libav
    ffmpeg
  ];

  # The test suite has extensive unit tests; integration tests needing a display/GPU are skipped
  doCheck = false;

  postInstall = ''
    # Install desktop entry
    install -Dm644 data/io.github.lgse.Strata.desktop $out/share/applications/io.github.lgse.Strata.desktop
    substituteInPlace $out/share/applications/io.github.lgse.Strata.desktop \
      --replace-fail "Exec=strata" "Exec=$out/bin/strata" \
      --replace-fail "TryExec=strata" "TryExec=$out/bin/strata"

    # Install application icon
    install -Dm644 data/icons/scalable/apps/io.github.lgse.Strata.svg $out/share/icons/hicolor/scalable/apps/io.github.lgse.Strata.svg

    # Install D-Bus service for org.freedesktop.FileManager1
    install -Dm644 data/io.github.lgse.Strata.FileManager1.service $out/share/dbus-1/services/io.github.lgse.Strata.FileManager1.service
    substituteInPlace $out/share/dbus-1/services/io.github.lgse.Strata.FileManager1.service \
      --replace-fail "Exec=strata" "Exec=$out/bin/strata"

    # Install package manager marker so Strata's in-app updater knows it is managed by Nix
    mkdir -p $out/share/strata
    cat <<EOF > $out/share/strata/install-source.toml
manager = "nix"
package = "strata"
channel = "stable"
update_command = "nh os switch"
EOF
  '';

  preFixup = ''
    gappsWrapperArgs+=(
      --prefix PATH : "${lib.makeBinPath [ bubblewrap ]}"
      --prefix GST_PLUGIN_SYSTEM_PATH_1_0 : "${lib.makeSearchPath "lib/gstreamer-1.0" [
        gst_all_1.gstreamer
        gst_all_1.gst-plugins-base
        gst_all_1.gst-plugins-good
        gst_all_1.gst-libav
      ]}"
    )
  '';

  meta = {
    description = "A fast, keyboard-first file manager for Linux";
    homepage = "https://github.com/lgse/strata";
    license = lib.licenses.mit;
    mainProgram = "strata";
    platforms = lib.platforms.linux;
  };
}
