#!/usr/bin/env python3
"""
Auto-commit watcher - Monitors all Go files in folder and auto-commits
Repository: https://github.com/Geltrax69/Learning_GO.git
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

def analyze_file(content, file_name):
    """Analyze file content and detect Go features"""
    features = []
    
    # Go packages and imports
    if 'import (' in content:
        features.append("imports")
    if 'package main' in content:
        features.append("main package")
    
    # Common Go features
    if 'func ' in content:
        features.append("functions")
    if 'struct {' in content or 'type ' in content:
        features.append("types")
    if 'interface {' in content:
        features.append("interface")
    if 'goroutine' in content or 'go func' in content or 'go ' in content:
        features.append("goroutines")
    if 'chan ' in content or 'channel' in content:
        features.append("channels")
    if 'defer ' in content:
        features.append("defer")
    
    # Common Go packages
    if '"fmt"' in content:
        features.append("fmt")
    if '"net/http"' in content:
        features.append("http")
    if '"encoding/json"' in content:
        features.append("json")
    if '"io"' in content or '"io/' in content:
        features.append("io")
    if '"os"' in content:
        features.append("os")
    if '"sync"' in content:
        features.append("sync")
    
    # Data structures
    if 'make(map' in content or 'map[' in content:
        features.append("map")
    if 'make([]' in content or '[]' in content:
        features.append("slice")
    if 'append(' in content:
        features.append("append")
    
    # Error handling
    if 'if err != nil' in content:
        features.append("error handling")
    
    return features


def commit_changes(file_path, repo_path):
    """Stage and commit changes"""
    try:
        file_name = os.path.basename(file_path)
        
        # Stage the file
        subprocess.run(['git', 'add', file_name], cwd=repo_path, 
                      capture_output=True, timeout=5)
        
        # Check if there are staged changes
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                              cwd=repo_path, timeout=5)
        
        if result.returncode != 0:  # There are changes
            # Read file to analyze
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect features
            features = analyze_file(content, file_name)
            
            feature_str = ", ".join(features[:3]) if features else "code update"
            base_name = os.path.splitext(file_name)[0]
            msg = f"Update {base_name}: {feature_str} ({len(content.split(chr(10)))} lines)"
            
            # Commit with proper author info for contribution counting
            result = subprocess.run(
                ['git', 'commit', '-m', msg, 
                 '--author=Geltrax69 <10lalitsingh01@gmail.com>'],
                cwd=repo_path, capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print(f"✓ Committed: {msg}")
                
                # Push to GitHub
                push_result = subprocess.run(['git', 'push', 'origin', 'main'], 
                                           cwd=repo_path, capture_output=True, text=True, timeout=10)
                if push_result.returncode == 0:
                    print(f"  📤 Pushed to GitHub")
                else:
                    print(f"  ⚠️  Push failed (check connection)")
                
                return True
    except Exception as e:
        print(f"Error: {e}")
    
    return False


def get_go_files(repo_path):
    """Get all Go files in the repository"""
    go_files = []
    for ext in ['*.go']:
        go_files.extend(Path(repo_path).glob(ext))
        # Also search subdirectories
        go_files.extend(Path(repo_path).glob(f'**/{ext}'))
    return [str(f) for f in go_files if f.is_file()]


def main():
    # Get repository path
    if len(sys.argv) < 2:
        repo_path = os.path.abspath(".")
    else:
        arg_path = os.path.abspath(sys.argv[1])
        if os.path.isfile(arg_path):
            repo_path = os.path.dirname(arg_path)
        else:
            repo_path = arg_path
    
    # Check git
    if not os.path.exists(os.path.join(repo_path, '.git')):
        print(f"Error: Not a git repository - {repo_path}")
        sys.exit(1)
    
    # Get all Go files
    go_files = get_go_files(repo_path)
    
    if not go_files:
        print(f"No Go files found in {repo_path}")
        sys.exit(1)
    
    print(f"🔍 Watching all Go files in: {repo_path}")
    print(f"📦 Repository: https://github.com/Geltrax69/Learning_GO.git")
    print(f"📄 Files tracked: {len(go_files)}")
    for f in go_files:
        print(f"   - {os.path.relpath(f, repo_path)}")
    print("Auto-commit enabled - Press Ctrl+C to stop\n")
    
    # Track last modification times
    file_mtimes = {}
    for f in go_files:
        try:
            file_mtimes[f] = os.path.getmtime(f)
        except OSError:
            file_mtimes[f] = 0
    
    try:
        while True:
            time.sleep(1)
            
            # Re-scan for new files
            current_go_files = get_go_files(repo_path)
            
            # Check for new files
            for f in current_go_files:
                if f not in file_mtimes:
                    print(f"📝 New file detected: {os.path.relpath(f, repo_path)}")
                    file_mtimes[f] = 0
            
            # Check each file for modifications
            for file_path in current_go_files:
                try:
                    current_mtime = os.path.getmtime(file_path)
                    last_mtime = file_mtimes.get(file_path, 0)
                    
                    if current_mtime > last_mtime:
                        file_mtimes[file_path] = current_mtime
                        if last_mtime > 0:  # Skip initial scan
                            time.sleep(0.5)  # Wait for file write to complete
                            print(f"📝 Changed: {os.path.relpath(file_path, repo_path)}")
                            commit_changes(file_path, repo_path)
                except OSError:
                    pass
            
    except KeyboardInterrupt:
        print("\n✓ Watcher stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
