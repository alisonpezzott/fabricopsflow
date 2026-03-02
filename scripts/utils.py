import os
import subprocess
from pathlib import Path, PurePosixPath
from typing import List, Optional, Set, Tuple


def _run(cmd: List[str], check: bool = True) -> str:
    """Run a command and return stdout."""
    p = subprocess.run(cmd, capture_output=True, text=True, check=check)
    if check and p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, output=p.stdout, stderr=p.stderr)
    return p.stdout.strip()


def _git_ref_exists(ref: str) -> bool:
    result = subprocess.run(["git", "rev-parse", "--verify", ref], capture_output=True, text=True)
    return result.returncode == 0


def _normalize_ref(ref: str) -> str:
    if ref.startswith("refs/heads/"):
        return f"origin/{ref[len('refs/heads/'):] }"
    return ref


def _ensure_remote_ref(ref: str) -> None:
    if not ref.startswith("origin/"):
        return
    branch = ref.split("/", 1)[1]
    _run(["git", "fetch", "--no-tags", "--prune", "--depth", "50", "origin", f"{branch}:{ref}"], check=False)


def get_changed_files(base_ref: str, head_ref: str) -> List[str]:
    """
    Returns the list of changed file paths between base_ref and head_ref.
    Paths are returned as POSIX-like strings (forward slashes), as Git prints them.
    """
    if base_ref and not _git_ref_exists(base_ref):
        _ensure_remote_ref(base_ref)
    if head_ref and not _git_ref_exists(head_ref):
        _ensure_remote_ref(head_ref)

    try:
        out = _run(["git", "diff", "--name-only", base_ref, head_ref])
    except subprocess.CalledProcessError:
        return []
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _find_platform_item(repo_rel_path: str, src_root: str) -> Optional[str]:
    p = PurePosixPath(repo_rel_path)
    if not p.parts or p.parts[0] != src_root:
        return None

    fs_path = Path(*p.parts)
    current = fs_path if fs_path.name == ".platform" else fs_path.parent
    src_path = Path(src_root)

    while True:
        if (current / ".platform").exists():
            return PurePosixPath(*current.parts).as_posix()
        if current == src_path or current.parent == current:
            break
        current = current.parent

    return None


def extract_src_items(changed_files: List[str], src_root: str = "src", return_full_path: bool = True) -> List[str]:
    """
    From a list of changed file paths, find the nearest ancestor under src_root
    that contains a .platform file.
    Example:
      src/data/lk_bronze.Lakehouse/anything/file.json -> src/data/lk_bronze.Lakehouse
    """
    items: Set[str] = set()

    for f in changed_files:
        platform_item = _find_platform_item(f, src_root)
        if not platform_item:
            continue

        if return_full_path:
            items.add(platform_item)
        else:
            rel = PurePosixPath(platform_item).relative_to(src_root).as_posix()
            items.add(rel)

    return sorted(items)


def resolve_head_and_prev() -> Tuple[str, str]:
    """
    Default strategy: compare current commit (HEAD) to previous commit (HEAD~1).
    In Azure DevOps pipelines this usually works for 'post-merge' builds too.
    """
    pr_target = os.getenv("SYSTEM_PULLREQUEST_TARGETBRANCH")
    if pr_target:
        target_ref = _normalize_ref(pr_target)
        return target_ref, "HEAD"

    depth_raw = os.getenv("DIFF_DEPTH", "1").strip()
    try:
        depth = max(1, int(depth_raw))
    except ValueError:
        depth = 1

    head = "HEAD"
    prev = f"HEAD~{depth}"
    return prev, head


def list_changed_src_items() -> List[str]:
    # Optional overrides via env vars (useful in pipelines)
    # Example: set DIFF_BASE=origin/main and DIFF_HEAD=HEAD
    # If not set, DIFF_DEPTH can override the default HEAD~1 (e.g., DIFF_DEPTH=3)
    base_ref = os.getenv("DIFF_BASE")
    head_ref = os.getenv("DIFF_HEAD")

    if not base_ref or not head_ref:
        base_ref, head_ref = resolve_head_and_prev()

    changed_files = get_changed_files(base_ref, head_ref)

    _src_items = extract_src_items(changed_files, src_root="src", return_full_path=True)
    src_items = [i for i in _src_items if not i.lower().endswith(".md")]

    return src_items

    # If you want a single-line output for later steps:
    # print("\n;".join(src_items))

