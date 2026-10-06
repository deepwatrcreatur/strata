// SPDX-License-Identifier: MIT

use std::{
    path::{Component, Path, PathBuf},
    process::Command,
};

// NixOS setuid wrappers must take precedence over store symlinks.
pub(crate) const SEARCH_ROOTS: &[&str] = &[
    "/run/wrappers/bin",
    "/usr/bin",
    "/usr/sbin",
    "/bin",
    "/sbin",
    "/run/current-system/sw/bin",
    "/run/current-system/profile/bin",
    "/run/booted-system/sw/bin",
    "/nix/var/nix/profiles/default/bin",
];

// NixOS wrappers are regular files, not store symlinks.
pub(crate) const TRUST_ROOTS: &[&str] = &[
    "/usr/bin",
    "/usr/sbin",
    "/bin",
    "/sbin",
    "/run/wrappers/bin",
    "/nix/store",
    "/gnu/store",
];

#[cfg(test)]
mod tests;

pub(crate) fn resolve(name: &str) -> Result<PathBuf, String> {
    let mut search: Vec<PathBuf> = SEARCH_ROOTS.iter().map(PathBuf::from).collect();
    if let Ok(user) = std::env::var("USER") {
        let per_user = PathBuf::from(format!("/etc/profiles/per-user/{user}/bin"));
        if per_user.is_dir() && !search.contains(&per_user) {
            search.push(per_user);
        }
    }
    if let Ok(home) = std::env::var("HOME") {
        let nix_profile = PathBuf::from(home).join(".nix-profile/bin");
        if nix_profile.is_dir() && !search.contains(&nix_profile) {
            search.push(nix_profile);
        }
    }
    if let Some(path_var) = std::env::var_os("PATH") {
        for path in std::env::split_paths(&path_var) {
            if !search.contains(&path) {
                search.push(path);
            }
        }
    }
    let search_refs: Vec<&Path> = search.iter().map(PathBuf::as_path).collect();
    let trust: Vec<&Path> = TRUST_ROOTS.iter().copied().map(Path::new).collect();
    resolve_in(name, &search_refs, &trust)
}

pub(crate) fn command(name: &str) -> Result<Command, String> {
    Ok(Command::new(resolve(name)?))
}

pub(crate) fn resolve_in(
    name: &str,
    search_roots: &[&Path],
    trust_roots: &[&Path],
) -> Result<PathBuf, String> {
    if !is_single_basename(name) {
        return Err("helper name must be a single basename".to_owned());
    }

    for dir in search_roots {
        let candidate = dir.join(name);
        if !candidate.is_file() {
            continue;
        }
        let Ok(canonical) = candidate.canonicalize() else {
            continue;
        };
        if sits_under(&canonical, trust_roots) {
            // Preserve argv0 for multicall binaries and profile wrappers.
            return Ok(found_path(candidate));
        }
    }

    Err(format!(
        "{name} was not found in a trusted system directory"
    ))
}

fn is_single_basename(name: &str) -> bool {
    if name.is_empty() || name.contains('/') || name.contains('\0') {
        return false;
    }
    matches!(
        Path::new(name).components().collect::<Vec<_>>().as_slice(),
        [Component::Normal(part)] if *part == name
    )
}

fn sits_under(canonical: &Path, trust_roots: &[&Path]) -> bool {
    trust_roots.iter().any(|root| {
        let root = match root.canonicalize() {
            Ok(path) => path,
            Err(_) if root.is_absolute() => (*root).to_path_buf(),
            Err(_) => return false,
        };
        canonical.starts_with(root)
    })
}

fn found_path(candidate: PathBuf) -> PathBuf {
    if candidate.is_absolute() {
        candidate
    } else {
        std::path::absolute(&candidate).unwrap_or(candidate)
    }
}
