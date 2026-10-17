"""Prevent working-tree checks from silently approving partially staged files."""
import subprocess


def main() -> int:
    probe = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True)
    if probe.returncode:
        print('No Git repository yet; staged-file checks skipped.')
        return 0
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
    staged = set(subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z']).split(b'\0'))
    unstaged = set(subprocess.check_output(['git', 'diff', '--name-only', '-z']).split(b'\0'))
    partial = (staged & unstaged) - {b''}
    if partial:
        print('Partially staged files: stage or stash remaining edits before validating:')
        for path in sorted(partial):
            print(path.decode(errors='replace'))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
