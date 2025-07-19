#!/usr/bin/env python3
"""
Script to clean up the old knowledge base implementation.

This script removes the old knowledge base implementation from src/agents/knowledge_base
after all components have been migrated to the new implementation in src/knowledge_base.
"""

import os
import shutil
import sys


def print_header(message):
    """Print a header message."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)


def print_info(message):
    """Print an info message."""
    print(f"[INFO] {message}")


def print_warning(message):
    """Print a warning message."""
    print(f"[WARNING] {message}")


def print_error(message):
    """Print an error message."""
    print(f"[ERROR] {message}")


def confirm(message):
    """Ask for confirmation."""
    response = input(f"{message} (y/n): ")
    return response.lower() in ("y", "yes")


def main():
    """Main function."""
    print_header("Knowledge Base Cleanup Script")
    print_info("This script will remove the old knowledge base implementation from src/agents/knowledge_base")
    print_info("Make sure you have migrated all components to the new implementation in src/knowledge_base")
    
    # Check if the old implementation exists
    old_path = os.path.join("src", "agents", "knowledge_base")
    if not os.path.exists(old_path):
        print_error(f"Old implementation not found at {old_path}")
        return 1
    
    # Check if the new implementation exists
    new_path = os.path.join("src", "knowledge_base")
    if not os.path.exists(new_path):
        print_error(f"New implementation not found at {new_path}")
        return 1
    
    # Ask for confirmation
    if not confirm("Are you sure you want to remove the old implementation?"):
        print_info("Cleanup aborted")
        return 0
    
    # Create a backup
    backup_path = os.path.join("src", "agents", "knowledge_base_backup")
    if os.path.exists(backup_path):
        print_warning(f"Backup already exists at {backup_path}")
        if confirm("Do you want to overwrite the existing backup?"):
            shutil.rmtree(backup_path)
        else:
            print_info("Cleanup aborted")
            return 0
    
    print_info(f"Creating backup at {backup_path}")
    shutil.copytree(old_path, backup_path)
    
    # Remove the old implementation
    print_info(f"Removing old implementation at {old_path}")
    shutil.rmtree(old_path)
    
    print_header("Cleanup completed successfully")
    print_info(f"The old implementation has been backed up to {backup_path}")
    print_info(f"You can restore it by running: mv {backup_path} {old_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())